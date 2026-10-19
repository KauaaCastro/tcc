import asyncio
import httpx
from typing import List, Optional
from app.config import settings
from app.utils.logger import logger


# Serviço de geração de vetores semânticos (768 dimensões) via Google Gemini Embeddings
class EmbeddingService:

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = settings.GEMINI_EMBEDDING_MODEL
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}"

    # Converte um texto único em vetor de 768 floats com taskType e retry exponencial
    async def get_embedding(
        self,
        text: str,
        task_type: str = "RETRIEVAL_DOCUMENT",
        max_retries: int = 3,
        initial_backoff: float = 2.0
    ) -> Optional[List[float]]:
        if not self.api_key:
            logger.error("[EMBEDDING] GEMINI_API_KEY não configurada no arquivo .env.")
            return None

        clean_text = text.strip()
        if not clean_text:
            return None

        url = f"{self.base_url}:embedContent"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": clean_text}]
            },
            "taskType": task_type,
            "output_dimensionality": 768
        }

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, headers=headers, json=payload)

                    if response.status_code == 200:
                        data = response.json()
                        return data.get("embedding", {}).get("values")
                    if response.status_code in (429, 503):
                        wait_time = initial_backoff * (2 ** attempt)
                        logger.warning(
                            f"[EMBEDDING] Status {response.status_code}. "
                            f"Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[EMBEDDING] Erro na API Gemini ({response.status_code}): {response.text[:250]}")
                        return None
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                wait_time = initial_backoff * (2 ** attempt)
                logger.warning(f"[EMBEDDING] Instabilidade de rede ({e}). Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"[EMBEDDING] Falha inesperada ao gerar embedding: {str(e)}")
                return None

        logger.error(f"[EMBEDDING] Falha definitiva ao gerar embedding após {max_retries} tentativas.")
        return None

    # Converte um lote de textos em vetores de 768 floats via batchEmbedContents
    async def get_embeddings_batch(
        self,
        texts: List[str],
        task_type: str = "RETRIEVAL_DOCUMENT",
        max_retries: int = 5,
        initial_backoff: float = 12.0
    ) -> Optional[List[List[float]]]:
        if not self.api_key or not texts:
            return None

        url = f"{self.base_url}:batchEmbedContents"
        headers = {
            "x-goog-api-key": self.api_key,
            "Content-Type": "application/json",
        }
        requests_payload = [
            {
                "model": f"models/{self.model}",
                "content": {"parts": [{"text": t.strip()}]},
                "taskType": task_type,
                "output_dimensionality": 768,
            }
            for t in texts
        ]

        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    response = await client.post(
                        url, headers=headers, json={"requests": requests_payload}
                    )
                    if response.status_code == 200:
                        items = response.json().get("embeddings", [])
                        vectors = [item.get("values") for item in items if item.get("values")]
                        return vectors if len(vectors) == len(texts) else None
                    if response.status_code in (429, 503):
                        wait_time = initial_backoff * (2 ** attempt)
                        logger.warning(
                            f"[EMBEDDING-BATCH] Status {response.status_code}. "
                            f"Tentativa {attempt + 1}/{max_retries}. Aguardando {wait_time:.1f}s..."
                        )
                        await asyncio.sleep(wait_time)
                    else:
                        logger.error(f"[EMBEDDING-BATCH] Erro ({response.status_code}): {response.text[:250]}")
                        return None
            except (httpx.TimeoutException, httpx.NetworkError) as e:
                wait_time = initial_backoff * (2 ** attempt)
                logger.warning(f"[EMBEDDING-BATCH] Instabilidade de rede ({e}). Aguardando {wait_time:.1f}s...")
                await asyncio.sleep(wait_time)
            except Exception as e:
                logger.error(f"[EMBEDDING-BATCH] Falha inesperada no lote: {str(e)}")
                return None

        return None


embedding_service = EmbeddingService()
