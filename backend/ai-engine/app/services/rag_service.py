from typing import List, Dict, Any
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.db.models import BulaChunk
from app.services.embedding_service import embedding_service
from app.utils.logger import logger


class RAGService:
    """
    Serviço responsável por recuperar contexto farmacológico usando busca 
    semântica vetorial (RAG) no PostgreSQL.
    """

    async def search_relevant_chunks(
        self,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
        """
        Recebe uma pergunta em texto puro e retorna os 'top_k' chunks mais relevantes.
        """
        query_vector = await embedding_service.get_embedding(query)

        if not query_vector:
            logger.warning(f"Não foi possível gerar embedding para a pergunta: '{query}'")
            return []

        async with AsyncSessionLocal() as session:
            stmt = (
                select(BulaChunk)
                .order_by(BulaChunk.embedding.cosine_distance(query_vector))
                .limit(top_k)
            )

            result = await session.execute(stmt)
            chunks = result.scalars().all()

rag_service = RAGService()


if __name__ == "__main__":
    import asyncio

    async def test_search():
        print("--- TESTE DE BUSCA SEMÂNTICA NO PGVECTOR (HNSW) ---")
        pergunta = "Quais as reações adversas e efeitos colaterais da Atorvastatina?"
        print(f"Pergunta de teste: '{pergunta}'\n")

        chunks = await rag_service.search_relevant_chunks(pergunta, top_k=2)
        if not chunks:
            print("[INFO] Nenhum chunk retornado. Certifique-se de que o banco está rodando e semeado.")
        else:
            print(f"[SUCESSO] {len(chunks)} trechos clínicos recuperados via similaridade de cosseno:")
            for i, chunk in enumerate(chunks, start=1):
                print(f"\nResultado {i}:")
                print(f"  Medicamento: {chunk.get('med_name')}")
                print(f"  Trecho: {chunk.get('content')[:200]}...")

    asyncio.run(test_search())

