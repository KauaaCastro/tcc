import asyncio
from pathlib import Path
from typing import Optional
from sqlalchemy import select

from app.db import init_db, AsyncSessionLocal, BulaChunk
from app.services.pdf_processor import PDFProcessor
from app.services.embedding_service import embedding_service
from app.utils.logger import logger


async def seed_bulario(limit: Optional[int] = 3) -> None:
    """
    Varre as bulas em PDF da pasta Script/bulario, extrai chunks,
    gera embeddings com o Gemini e grava no PostgreSQL via PGVector.
    
    :param limit: Quantidade máxima de medicamentos a processar (útil para testes rápidos).
    """
    logger.info("[SEED] Iniciando preparacao do banco de dados...")

    await init_db()

    BASE_DIR = Path(__file__).resolve().parents[4]
    bulario_dir = BASE_DIR / "Script" / "bulario"

    if not bulario_dir.exists():
        logger.error(f"[SEED] Diretorio de bulas nao encontrado em: {bulario_dir}")
        return

    pdf_files = sorted(list(bulario_dir.glob("*.pdf")))
    if limit:
        pdf_files = pdf_files[:limit]

    logger.info(f"[SEED] Encontrados {len(pdf_files)} medicamentos para processar.")

    async with AsyncSessionLocal() as session:
        for index, pdf_file in enumerate(pdf_files, start=1):
            med_name = PDFProcessor.clean_medication_name(pdf_file)

            query = select(BulaChunk).where(BulaChunk.med_name == med_name)
            result = await session.execute(query)
            existing = result.scalars().first()

            if existing:
                print(f"[{index}/{len(pdf_files)}] [PULANDO] '{med_name}' ja esta cadastrado no banco.")
                continue

            print(f"\n[{index}/{len(pdf_files)}] [PROCESSANDO] Extraindo texto de: {med_name}...")
            chunks = PDFProcessor.process_single_pdf(pdf_file)
            print(f"-> {len(chunks)} chunks gerados. Gerando vetores com Gemini...")

            records_to_insert = []
            for item in chunks:
                vector = await embedding_service.get_embedding(item["content"])

                await asyncio.sleep(0.2)

                if vector:
                    chunk_record = BulaChunk(
                        med_name=item["med_name"],
                        chunk_index=item["chunk_index"],
                        content=item["content"],
                        embedding=vector,
                    )
                    records_to_insert.append(chunk_record)

            if records_to_insert:
                session.add_all(records_to_insert)
                await session.commit()
                print(f"[OK] '{med_name}' gravado com sucesso ({len(records_to_insert)} vetores salvos)!")
            else:
                logger.warning(f"[SEED] Nenhum vetor gerado para '{med_name}'.")

    logger.info("[SEED] Processo de povoamento concluido com sucesso!")


if __name__ == "__main__":
    asyncio.run(seed_bulario(limit=3))
