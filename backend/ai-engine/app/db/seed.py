import asyncio
from pathlib import Path
from typing import Optional
from sqlalchemy import select

from app.db.session import init_db, AsyncSessionLocal
from app.db.models import BulaChunk
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

    total_files = len(pdf_files)
    logger.info(f"[SEED] Iniciando processamento de {total_files} medicamentos...")

    processed_count = 0
    total_chunks_saved = 0

    async with AsyncSessionLocal() as session:
        for index, pdf_file in enumerate(pdf_files, start=1):
            percent = (index / total_files) * 100
            med_name = PDFProcessor.clean_medication_name(pdf_file)

            try:
                # Verifica se a bula já foi processada anteriormente
                query = select(BulaChunk).where(BulaChunk.med_name == med_name)
                result = await session.execute(query)
                existing = result.scalars().first()

                if existing:
                    logger.info(f"[{index}/{total_files} | {percent:.1f}%] [PULANDO] '{med_name}' já cadastrado.")
                    continue

                logger.info(f"[{index}/{total_files} | {percent:.1f}%] [PROCESSANDO] Extraindo texto de: '{med_name}'...")
                chunks = PDFProcessor.process_single_pdf(pdf_file)
                logger.info(f"-> {len(chunks)} chunks gerados para '{med_name}'. Gerando embeddings com Gemini...")

                records_to_insert = []
                for chunk_idx, item in enumerate(chunks, start=1):
                    vector = await embedding_service.get_embedding(item["content"])

                    # Pausa segura de 0.3s entre chamadas para respeitar o Rate-Limit
                    await asyncio.sleep(0.3)

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
                    processed_count += 1
                    total_chunks_saved += len(records_to_insert)
                    logger.info(f"[OK] '{med_name}' gravado com sucesso ({len(records_to_insert)} chunks salvos)!")
                else:
                    logger.warning(f"[SEED] Nenhum vetor gerado para '{med_name}'.")

            except Exception as e:
                logger.error(f"[ERRO] Falha ao processar medicamento '{med_name}': {str(e)}")
                await session.rollback()
                continue

    logger.info(
        f"[SEED CONCLUÍDO] Total de remédios processados nesta rodada: {processed_count} | "
        f"Total de chunks gravados: {total_chunks_saved}"
    )


if __name__ == "__main__":
    asyncio.run(seed_bulario(limit=3))
