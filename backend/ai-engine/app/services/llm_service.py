import json
from typing import AsyncGenerator, Optional
import httpx
from app.config import settings
from app.utils.logger import logger


class LLMService:
    """
    Serviço de comunicação com o LLM (Google Gemini 1.5 Flash).
    Suporta tanto geração completa quanto streaming assíncrono token por token (SSE).
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-1.5-flash"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"

    def _build_payload(self, system_prompt: str, user_question: str) -> dict:
        """Monta o payload no formato exigido pela API do Gemini v1beta."""
        return {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [{"text": user_question}]
                }
            ],
            "generationConfig": {
                "temperature": 0.2,       # Baixa temperatura para evitar alucinações médicas
                "topP": 0.8,
                "maxOutputTokens": 2048,
            }
        }

    async def generate_response_stream(
        self,
        system_prompt: str,
        user_question: str
    ) -> AsyncGenerator[str, None]:
        """
        Gera resposta em fluxo contínuo (Streaming SSE), emitindo cada fragmento
        de texto em tempo real conforme gerado pelo Gemini.
        """
        if not self.api_key:
            logger.error("[LLM] GEMINI_API_KEY não configurada no arquivo .env.")
            yield "Erro de configuração: Chave da API Gemini ausente."
            return

        url = f"{self.base_url}:streamGenerateContent?alt=sse&key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = self._build_payload(system_prompt, user_question)

        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                async with client.stream("POST", url, headers=headers, json=payload) as response:
                    if response.status_code != 200:
                        error_text = await response.aread()
                        logger.error(
                            f"[LLM] Erro na API Gemini ({response.status_code}): "
                            f"{error_text.decode('utf-8', errors='ignore')}"
                        )
                        yield "Não foi possível obter a resposta da IA no momento."
                        return

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
                                    text_chunk = part.get("text", "")
                                    if text_chunk:
                                        yield text_chunk
                        except json.JSONDecodeError:
                            continue

        except Exception as e:
            logger.error(f"[LLM] Falha de conexão durante o streaming do Gemini: {str(e)}")
            yield f"\n[Conexão interrompida com o serviço de IA: {str(e)}]"

    async def generate_response(
        self,
        system_prompt: str,
        user_question: str
    ) -> Optional[str]:
        """
        Gera a resposta completa de uma só vez (modo não-streaming).
        """
        full_text = []
        async for chunk in self.generate_response_stream(system_prompt, user_question):
            full_text.append(chunk)
        return "".join(full_text) if full_text else None


# Instância global reutilizável
llm_service = LLMService()


# Bloco para testar localmente
if __name__ == "__main__":
    import asyncio

    async def testar():
        print("--- TESTANDO STREAMING DO GEMINI 1.5 FLASH ---")
        prompt_sistema = "Você é um farmacêutico especialista. Responda de forma concisa."
        pergunta = "Qual a indicação principal da Dipirona e contraindicações básicas?"

        print("Recebendo resposta em tempo real:\n")
        async for fragmento in llm_service.generate_response_stream(prompt_sistema, pergunta):
            print(fragmento, end="", flush=True)
        print("\n\n--- FIM DO TESTE ---")

    asyncio.run(testar())
