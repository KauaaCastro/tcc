import httpx
import json
from typing import AsyncGenerator, Dict, Any, List, Optional
from app.config import settings
from app.schemas.user import UserProfileType
from app.schemas.error import AlertType, TrustedSourceLink
from app.services.prompt_service import prompt_service
from app.utils.logger import logger
from app.utils.sse import format_sse_event

OFFICIAL_TRUSTED_SOURCES = [
    TrustedSourceLink(
        name="Bulário Eletrônico da ANVISA",
        url="https://consultas.anvisa.gov.br/#/bulario/"
    ),
    TrustedSourceLink(
        name="Ministério da Saúde - Uso Racional de Medicamentos",
        url="https://www.gov.br/saude/pt-br/assuntos/saude-de-a-a-z/m/medicamentos"
    )
]

class AIService:
    def __init__(self):
        self.gemini_api_key = settings.GEMINI_API_KEY
        self.anthropic_api_key = settings.ANTHROPIC_API_KEY

    async def generate_response(
        self,
        message: str,
        profile_type: UserProfileType = UserProfileType.PATIENT,
        rag_context: str = ""
    ) -> Dict[str, Any]:
        """
        Orchestrates AI response generation: Gemini -> Claude -> Safe Fallback.
        """
        system_prompt = prompt_service.build_system_prompt(profile_type, rag_context)

        # 1. Try Gemini
        if self.gemini_api_key:
            try:
                gemini_res = await self._call_gemini_api(system_prompt, message)
                if gemini_res:
                    return {
                        "answer": gemini_res,
                        "alert_type": AlertType.INFO,
                        "profile_type": profile_type,
                        "trusted_sources": OFFICIAL_TRUSTED_SOURCES
                    }
            except Exception as e:
                logger.error(f"Gemini API execution failed: {str(e)}")

        # 2. Try Claude (Redundancy)
        if self.anthropic_api_key:
            try:
                claude_res = await self._call_claude_api(system_prompt, message)
                if claude_res:
                    return {
                        "answer": claude_res,
                        "alert_type": AlertType.INFO,
                        "profile_type": profile_type,
                        "trusted_sources": OFFICIAL_TRUSTED_SOURCES
                    }
            except Exception as e:
                logger.error(f"Claude API execution failed: {str(e)}")

        # 3. Safe Fallback (Guaranteed response without fake simulations)
        return self._get_safe_fallback_response(profile_type)

    async def generate_streaming_response(
        self,
        message: str,
        profile_type: UserProfileType = UserProfileType.PATIENT,
        rag_context: str = ""
    ) -> AsyncGenerator[str, None]:
        """
        Orchestrates SSE streaming response token by token.
        """
        system_prompt = prompt_service.build_system_prompt(profile_type, rag_context)

        if self.gemini_api_key:
            try:
                async for chunk in self._stream_gemini_api(system_prompt, message):
                    yield format_sse_event("delta", {"content": chunk})
                
                yield format_sse_event("done", {
                    "alert_type": AlertType.INFO,
                    "profile_type": profile_type,
                    "trusted_sources": [s.model_dump() for s in OFFICIAL_TRUSTED_SOURCES]
                })
                return
            except Exception as e:
                logger.error(f"Gemini Streaming failed: {str(e)}")

        # Fallback for streaming
        fallback = self._get_safe_fallback_response(profile_type)
        yield format_sse_event("delta", {"content": fallback["answer"]})
        yield format_sse_event("done", {
            "alert_type": fallback["alert_type"],
            "profile_type": profile_type,
            "trusted_sources": [s.model_dump() for s in OFFICIAL_TRUSTED_SOURCES]
        })

    async def _call_gemini_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_message}]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                candidates = data.get("candidates", [])
                if candidates:
                    parts = candidates[0].get("content", {}).get("parts", [])
                    if parts:
                        return parts[0].get("text", "")
            else:
                logger.warning(f"Gemini API HTTP Error {response.status_code}: {response.text}")
        return None

    async def _stream_gemini_api(self, system_prompt: str, user_message: str) -> AsyncGenerator[str, None]:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:streamGenerateContent?alt=sse&key={self.gemini_api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {
                "parts": [{"text": system_prompt}]
            },
            "contents": [
                {
                    "parts": [{"text": user_message}]
                }
            ]
        }
        async with httpx.AsyncClient(timeout=60.0) as client:
            async with client.stream("POST", url, json=payload, headers=headers) as response:
                if response.status_code != 200:
                    raise Exception(f"Gemini stream HTTP Error {response.status_code}")
                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        data_str = line[6:].strip()
                        if data_str == "[DONE]":
                            break
                        try:
                            data_json = json.loads(data_str)
                            candidates = data_json.get("candidates", [])
                            if candidates:
                                parts = candidates[0].get("content", {}).get("parts", [])
                                if parts:
                                    text_chunk = parts[0].get("text", "")
                                    if text_chunk:
                                        yield text_chunk
                        except Exception:
                            continue

    async def _call_claude_api(self, system_prompt: str, user_message: str) -> Optional[str]:
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "x-api-key": self.anthropic_api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        payload = {
            "model": "claude-3-haiku-20240307",
            "max_tokens": 1024,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_message}]
        }
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
            if response.status_code == 200:
                data = response.json()
                content = data.get("content", [])
                if content:
                    return content[0].get("text", "")
        return None

    def _get_safe_fallback_response(self, profile_type: UserProfileType) -> Dict[str, Any]:
        """
        Fallback seguro exigido pelas diretrizes do projeto:
        Nunca inventar simulações fictícias; responder com alert_type: "restriction" e links oficiais.
        """
        fallback_msg = (
            "Não foi possível processar a consulta em tempo real no momento devido a uma instabilidade temporária nos serviços de IA. "
            "Para garantir a sua segurança clínica, não fornecemos simulações fictícias de bulas ou dosagens. "
            "Por favor, consulte o Bulário Eletrônico oficial da ANVISA ou procure orientação de um profissional de saúde registrado."
        )
        return {
            "answer": fallback_msg,
            "alert_type": AlertType.RESTRICTION,
            "profile_type": profile_type,
            "trusted_sources": OFFICIAL_TRUSTED_SOURCES
        }

ai_service = AIService()
