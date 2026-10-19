import asyncio
import json
from typing import AsyncGenerator, Optional, Tuple
import httpx
from app.config import settings
from app.utils.logger import logger


# Exceção lançada quando a API de IA está indisponível para acionar o Fallback Seguro
class LLMUnavailableError(Exception):
    pass


# Serviço de comunicação assíncrona com o Google Gemini (streaming SSE e resposta completa)
class LLMService:

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_MODEL
        self.fallback_model = settings.GEMINI_FALLBACK_MODEL
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"

    # Separa as instruções de sistema das tags XML do Prompt Sanduíche para não duplicar a pergunta
    @staticmethod
    def _split_sandwich_prompt(system_prompt: str, user_question: str) -> Tuple[str, str]:
        marker = "<perfil_paciente>"
        if marker in system_prompt:
            idx = system_prompt.index(marker)
            instructions = system_prompt[:idx].strip()
            xml_context = system_prompt[idx:].strip()
            return instructions, xml_context
        return system_prompt, user_question

    # Monta o payload JSON com temperatura baixa (0.2) e limite amplo de saída (4096 tokens)
    def _build_payload(self, system_prompt: str, user_question: str) -> dict:
        instructions, user_content = self._split_sandwich_prompt(system_prompt, user_question)
        return {
            "system_instruction": {
                "parts": [{"text": instructions}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_content}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,
                "topP": 0.8,
                "maxOutputTokens": 4096,
            }
        }

    # Transmite os fragmentos de texto gerados pelo Gemini via SSE com retry e modelo de reserva
    async def generate_response_stream(
        self,
        system_prompt: str,
        user_question: str
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            logger.error("[LLM] GEMINI_API_KEY não configurada no arquivo .env.")
            raise LLMUnavailableError("Chave da API Gemini ausente.")

        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = self._build_payload(system_prompt, user_question)
        models_to_try = [self.model]
        if self.fallback_model and self.fallback_model != self.model:
            models_to_try.append(self.fallback_model)

        last_error = "Serviço de IA indisponível."
        for model_name in models_to_try:
            url = f"{self.base_url}/{model_name}:streamGenerateContent?alt=sse"
            for attempt in range(2):
                emitted_any = False
                try:
                    async with httpx.AsyncClient(timeout=60.0) as client:
                        async with client.stream("POST", url, headers=headers, json=payload) as response:
                            if response.status_code in (429, 503) and attempt == 0:
                                wait_s = 1.5 * (attempt + 1)
                                logger.warning(f"[LLM] Status {response.status_code} em {model_name}. Retentando em {wait_s}s...")
                                await asyncio.sleep(wait_s)
                                continue

                            if response.status_code != 200:
                                error_text = await response.aread()
                                last_error = f"HTTP {response.status_code} ({model_name})"
                                logger.error(
                                    f"[LLM] Erro na API Gemini ({response.status_code} - {model_name}): "
                                    f"{error_text.decode('utf-8', errors='ignore')[:250]}"
                                )
                                break

                            async for line in response.aiter_lines():
                                if not line or not line.startswith("data: "):
                                    continue

                                data_str = line[6:].strip()
                                if data_str == "[DONE]":
                                    break

                                try:
                                    data_json = json.loads(data_str)
                                    candidates = data_json.get("candidates", [])
                                    if candidates:
                                        parts = candidates[0].get("content", {}).get("parts", [])
                                        for part in parts:
                                            if part.get("thought"):
                                                continue
                                            text_chunk = part.get("text", "")
                                            if text_chunk:
                                                emitted_any = True
                                                yield text_chunk
                                except json.JSONDecodeError:
                                    continue

                            if emitted_any:
                                return
                            last_error = f"Resposta vazia do modelo {model_name}."
                            break

                except (httpx.TimeoutException, httpx.NetworkError) as e:
                    last_error = f"Falha de rede ({str(e)})"
                    logger.warning(f"[LLM] Instabilidade de rede em {model_name}: {e}")
                    if emitted_any:
                        raise LLMUnavailableError(last_error) from e
                    if attempt == 0:
                        await asyncio.sleep(1.5)
                        continue
                    break
                except LLMUnavailableError:
                    raise
                except Exception as e:
                    last_error = str(e)
                    logger.error(f"[LLM] Falha inesperada no streaming ({model_name}): {e}")
                    break

        raise LLMUnavailableError(last_error)

    # Gera a resposta completa consumindo o gerador assíncrono de streaming
    async def generate_response(
        self,
        system_prompt: str,
        user_question: str
    ) -> str:
        full_text = []
        async for chunk in self.generate_response_stream(system_prompt, user_question):
            full_text.append(chunk)
        result = "".join(full_text).strip()
        if not result:
            raise LLMUnavailableError("Resposta vazia retornada pelo modelo.")
        return result


llm_service = LLMService()
