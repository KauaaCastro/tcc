import argparse
import asyncio
from pathlib import Path
from typing import List, Optional
from sqlalchemy import delete, func, select

from app.db.session import init_db, AsyncSessionLocal
from app.db.models import BulaChunk
from app.services.pdf_processor import PDFProcessor
from app.services.embedding_service import embedding_service
from app.utils.logger import logger

# Lista prioritária de bulas essenciais para a demonstração clínica do TCC
PRIORITY_STEMS: List[str] = [
    "bula_claritromicina",
    "bula_sinvastatina",
    "bula_atorvastatina-calcica",
    "bula_acido-acetilsalicilico",
    "bula_dipirona-monoidratada",
    "bula_paracetamol",
    "bula_ibuprofeno",
    "bula_diclofenaco-sodico",
    "bula_digoxina",
    "bula_captopril",
    "bula_maleato-de-enalapril",
    "bula_cloridrato-de-metformina",
    "bula_cloridrato-de-fluoxetina",
    "bula_cloridrato-de-sertralina",
    "bula_cloridrato-de-tramadol",
    "bula_amoxicilina",
    "bula_amoxicilina-+-clavulanato-de-potassio",
    "bula_1779123722895",
    "bula_1779131037502",
]


# Ordena os arquivos PDF priorizando os medicamentos da lista principal
def sort_pdfs_by_priority(pdf_files: List[Path]) -> List[Path]:
    priority_map = {stem: idx for idx, stem in enumerate(PRIORITY_STEMS)}
    return sorted(
        pdf_files,
        key=lambda p: (0, priority_map[p.stem]) if p.stem in priority_map else (1, p.stem)
    )


# Varre as bulas em PDF, extrai chunks, gera embeddings em lote e grava de forma atômica por bula
async def seed_bulario(
    limit: Optional[int] = 9,
    max_chunks: int = 850,
    batch_size: int = 20
) -> None:
    logger.info("[SEED] Iniciando preparacao do banco de dados...")
    await init_db()

    base_dir = Path(__file__).resolve().parents[4]
    bulario_dir = base_dir / "Script" / "bulario"

    if not bulario_dir.exists():
        logger.error(f"[SEED] Diretorio de bulas nao encontrado em: {bulario_dir}")
        return

    pdf_files = sort_pdfs_by_priority(list(bulario_dir.glob("*.pdf")))
    if limit:
        pdf_files = pdf_files[:limit]

    total_files = len(pdf_files)
    logger.info(
        f"[SEED] Iniciando processamento de ate {total_files} medicamentos "
        f"(teto de seguranca: {max_chunks} chunks nesta execucao)..."
    )

    processed_count = 0
    skipped_count = 0
    empty_count = 0
    failed_count = 0
    total_chunks_saved = 0

    async with AsyncSessionLocal() as session:
        for index, pdf_file in enumerate(pdf_files, start=1):
            percent = (index / total_files) * 100
            med_name = PDFProcessor.clean_medication_name(pdf_file)

            try:
                chunks = PDFProcessor.process_single_pdf(pdf_file)
                expected_chunks = len(chunks)

                if expected_chunks == 0:
                    logger.warning(f"[{index}/{total_files}] [VAZIO] PDF '{pdf_file.name}' sem texto extraivel.")
                    empty_count += 1
                    continue

                # Verifica a quantidade de chunks já gravados no banco para esta bula
                count_stmt = select(func.count()).select_from(BulaChunk).where(BulaChunk.med_name == med_name)
                existing_count = (await session.execute(count_stmt)).scalar_one()

                if existing_count == expected_chunks:
                    logger.info(
                        f"[{index}/{total_files} | {percent:.1f}%] [PULANDO] "
                        f"'{med_name}' ja completo ({existing_count} chunks)."
                    )
                    skipped_count += 1
                    continue

                if existing_count > 0:
                    logger.warning(
                        f"[{index}/{total_files}] [REPROCESSANDO] '{med_name}' estava incompleto "
                        f"({existing_count}/{expected_chunks} chunks). Limpando registros parciais..."
                    )
                    await session.execute(delete(BulaChunk).where(BulaChunk.med_name == med_name))
                    await session.commit()

                if total_chunks_saved + expected_chunks > max_chunks:
                    logger.info(
                        f"[SEED] Teto de cota ({max_chunks} chunks) atingido antes de '{med_name}' "
                        f"({expected_chunks} chunks). Encerrando rodada com seguranca."
                    )
                    break

                logger.info(
                    f"[{index}/{total_files} | {percent:.1f}%] [PROCESSANDO] "
                    f"'{med_name}' ({expected_chunks} chunks em lotes de {batch_size})..."
                )

                records_to_insert = []
                bula_failed = False

                for start_idx in range(0, expected_chunks, batch_size):
                    batch_items = chunks[start_idx:start_idx + batch_size]
                    batch_texts = [item["content"] for item in batch_items]

                    vectors = await embedding_service.get_embeddings_batch(
                        batch_texts,
                        task_type="RETRIEVAL_DOCUMENT"
                    )

                    if not vectors or len(vectors) != len(batch_items):
                        logger.error(
                            f"[ERRO] Falha ao vetorizar lote {start_idx // batch_size + 1} "
                            f"de '{med_name}'. Descartando bula parcial."
                        )
                        bula_failed = True
                        break

                    for item, vector in zip(batch_items, vectors):
                        records_to_insert.append(
                            BulaChunk(
                                med_name=item["med_name"],
                                chunk_index=item["chunk_index"],
                                content=item["content"],
                                embedding=vector,
                            )
                        )

                    # Pausa controlada entre lotes para respeitar a janela de 100 itens/min da camada gratuita
                    if start_idx + batch_size < expected_chunks:
                        await asyncio.sleep(4.5)

                if not bula_failed and len(records_to_insert) == expected_chunks:
                    session.add_all(records_to_insert)
                    await session.commit()
                    processed_count += 1
                    total_chunks_saved += len(records_to_insert)
                    logger.info(
                        f"[OK] '{med_name}' gravado integralmente "
                        f"({len(records_to_insert)} chunks | acumulado na sessao: {total_chunks_saved})."
                    )
                else:
                    await session.rollback()
                    failed_count += 1

            except Exception as e:
                logger.error(f"[ERRO] Falha ao processar medicamento '{med_name}': {str(e)}")
                await session.rollback()
                failed_count += 1
                continue

    logger.info(
        f"[SEED CONCLUIDO] Gravados: {processed_count} | Pulados (ja completos): {skipped_count} | "
        f"PDFs vazios: {empty_count} | Falhas: {failed_count} | Chunks salvos na rodada: {total_chunks_saved}"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Seed prioritario do bulario ANVISA no PGVector.")
    parser.add_argument("--limit", type=int, default=9, help="Maximo de PDFs a inspecionar (0 para todos).")
    parser.add_argument("--max-chunks", type=int, default=850, help="Teto de chunks a vetorizar na execucao.")
    parser.add_argument("--batch-size", type=int, default=20, help="Quantidade de textos por chamada em lote.")
    args = parser.parse_args()

    effective_limit = None if args.limit == 0 else args.limit
    asyncio.run(seed_bulario(limit=effective_limit, max_chunks=args.max_chunks, batch_size=args.batch_size))
