import asyncio 
import httpx
from typing import List, Optional
from app.config import settings
from app.utils.logger import logger

class EmbeddingService:
    """
    Serviço responsável por se comunicar com a API do Google Gemini
    para converter textos (chunks de bulas ou perguntas de usuários)
    em vetores numéricos de 768 dimensões (Embeddings).
    """

    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.model = "gemini-embedding-001"
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:embedContent"
        
    async def get_embedding(self, text: str) -> Optional[List[float]]:
        """
        Recebe um texto e retorna uma lista de 768 floats (o vetor
        semântico), ou None caso ocorra erro.
        """
        if not self.api_key:
            logger.error("GEMINI_API_KEY não configurada no arquivo .env.")
            return None
        
        clean_text = text.strip()
        
        if not clean_text:
            return None
        
        url = f"{self.base_url}?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "model": f"models/{self.model}",
            "content": {
                "parts": [{"text": clean_text}]
            },
            "output_dimensionality": 768
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    logger.error(f"Erro na API Gemini ({response.status_code}): {response.text}")
                    return None
                
                data = response.json()
                
                values = data.get("embedding", {}).get("values")
                return values
            
        except Exception as e: 
            logger.error(f"Falha de conexão ao gerar o embedding: {str(e)}")
            return None
        
embedding_service = EmbeddingService()
    
# Bloco para teste de funcionamento do arquivo
if __name__ == "__main__":
    async def testar():
        print("Testando a geração de vetor com o Gemini...")
        frase_teste = "Dipirona monoidratada é indicada como analgésico e antipirético."
        vetor = await embedding_service.get_embedding(frase_teste)
        
        if vetor:
            print("[OK] Sucesso! Vetor gerado.")
            print(f"Dimensao do vetor: {len(vetor)} numeros (deve ser 768)")
            print(f"Primeiros 5 valores do vetor: {vetor[:5]}...")
        else:
            print("[ERRO] Falha ao gerar o vetor. Verifique sua GEMINI_API_KEY no .env.")
            
    asyncio.run(testar())
