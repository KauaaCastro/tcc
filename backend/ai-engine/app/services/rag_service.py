from pathlib import Path
import re
import unicodedata
from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.db.models import BulaChunk, UserRegister, FarmHistory, HistoricoConsultas
from app.schemas.chat import PerfilUsuarioPayload
from app.services.embedding_service import embedding_service
from app.services.pdf_processor import PDFProcessor
from app.services.prompt_service import prompt_service
from app.utils.logger import logger


# Mapeia nomes comerciais populares para os princípios ativos correspondentes nas bulas
BRAND_ALIASES: Dict[str, str] = {
    "aas": "acido acetilsalicilico",
    "aspirina": "acido acetilsalicilico",
    "tylenol": "paracetamol",
    "novalgina": "dipirona monoidratada",
    "dorflex": "dipirona monoidratada",
    "advil": "ibuprofeno",
    "alivium": "ibuprofeno",
    "cataflam": "diclofenaco sodico",
    "voltaren": "diclofenaco sodico",
    "rivotril": "clonazepam",
    "lexotan": "bromazepam",
    "frontal": "alprazolam",
    "glifage": "cloridrato de metformina",
    "prozac": "cloridrato de fluoxetina",
    "zoloft": "cloridrato de sertralina",
    "marevan": "varfarina sodica",
    "coumadin": "varfarina sodica",
    "plasil": "cloridrato de metoclopramida",
    "vonau": "cloridrato de ondansetrona",
    "dramin": "dimenidrinato",
    "buscopan": "butilbrometo de escopolamina",
    "lasix": "furosemida",
    "puran": "levotiroxina sodica",
}


# Serviço de busca de bulas (PGVector + fallback local de PDF sem gastar tokens) e histórico
class RAGService:

    _local_pdf_cache: Dict[str, List[Dict[str, Any]]] = {}

    @staticmethod
    def _strip_accents(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(c for c in normalized if not unicodedata.combining(c))

    # Identifica possíveis medicamentos na pergunta, convertendo nomes comerciais em princípio ativo
    @classmethod
    def _extract_candidate_terms(cls, query: str, medications: Optional[List[str]] = None) -> List[str]:
        stopwords = {
            "posso", "tomar", "usar", "junto", "juntos", "entre", "interacao", "interacoes",
            "efeito", "efeitos", "colateral", "colaterais", "reacao", "reacoes", "risco",
            "riscos", "bula", "remedio", "remedios", "medicamento", "medicamentos", "comprimido",
            "gotas", "xarope", "para", "serve", "como", "qual", "quais", "quando", "porque",
            "tenho", "estou", "fazer", "causa", "pode", "podem", "deve", "devem", "adulto",
            "crianca", "idoso", "gestante", "gravida", "lactante", "pressao", "diabetes",
            "problema", "problemas", "saude", "alergia", "dose", "dosagem", "posologia",
            "dengue", "gastrite", "ulcera", "asma", "sinusite", "rinite", "febre", "dores",
            "cabeca", "estomago", "figado", "renal", "cardiaca", "cardiaco", "hipertensao",
            "depressao", "ansiedade", "insonia", "gripe", "infeccao", "inflamacao", "misturar"
        }
        candidates: List[str] = []

        def add_candidate(term: str) -> None:
            clean = cls._strip_accents(term.strip()).lower()
            mapped = BRAND_ALIASES.get(clean, clean)
            if len(mapped) >= 3 and mapped not in [c.lower() for c in candidates]:
                candidates.append(mapped)

        for med in (medications or []):
            if med and str(med).strip():
                add_candidate(str(med))

        raw_words = re.findall(r"[A-Za-zÀ-ÿ]{3,}", query or "")
        for word in raw_words:
            clean_word = cls._strip_accents(word).lower()
            if clean_word in BRAND_ALIASES:
                add_candidate(BRAND_ALIASES[clean_word])
            elif len(clean_word) >= 5 and clean_word not in stopwords:
                add_candidate(clean_word)

        return candidates[:6]

    # Lê localmente o PDF em Script/bulario/ sem gastar tokens da API de embedding
    @classmethod
    def _fallback_chunks_from_local_pdf(
        cls,
        med_term: str,
        query: str,
        max_chunks: int = 3
    ) -> List[Dict[str, Any]]:
        bulario_dir = Path(__file__).resolve().parents[4] / "Script" / "bulario"
        if not bulario_dir.exists():
            return []

        slug = cls._strip_accents(med_term).lower().strip().replace(" ", "-")
        matches = [
            p for p in bulario_dir.glob("*.pdf")
            if slug in cls._strip_accents(p.stem).lower()
        ]
        if not matches:
            return []

        pdf_file = matches[0]
        cache_key = pdf_file.name
        if cache_key not in cls._local_pdf_cache:
            try:
                cls._local_pdf_cache[cache_key] = PDFProcessor.process_single_pdf(pdf_file)
            except Exception as e:
                logger.warning(f"[RAG-LOCAL] Falha ao ler PDF local '{pdf_file.name}': {e}")
                return []

        all_chunks = cls._local_pdf_cache[cache_key]
        if not all_chunks:
            return []

        query_terms = [
            cls._strip_accents(w).lower()
            for w in re.findall(r"[A-Za-zÀ-ÿ]{4,}", query or "")
        ]
        safety_headers = (
            "interacoes medicamentosas",
            "contraindicacoes",
            "advertencias e precaucoes",
            "para que este medicamento e indicado",
            "posologia",
            "reacoes adversas",
        )

        def score_chunk(chunk: Dict[str, Any]) -> int:
            text_norm = cls._strip_accents(chunk.get("content", "")).lower()
            score = sum(3 for h in safety_headers if h in text_norm)
            score += sum(2 for qt in query_terms if qt in text_norm)
            return score

        ranked = sorted(all_chunks, key=score_chunk, reverse=True)
        return ranked[:max_chunks]

    # Busca os trechos de bula no PGVector e complementa com leitura local de PDF quando necessário
    async def search_relevant_chunks(
        self,
        query: str,
        top_k: int = 6,
        medications: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        meds_clean = [str(m).strip() for m in (medications or []) if m and str(m).strip()]
        candidates = self._extract_candidate_terms(query, meds_clean)
        enriched_query = f"{', '.join(candidates)}: {query}" if candidates else query

        query_vector = await embedding_service.get_embedding(
            enriched_query, task_type="RETRIEVAL_QUERY"
        )

        collected: List[Dict[str, Any]] = []
        seen_keys = set()

        def add_chunk_dict(c_dict: Dict[str, Any]) -> None:
            key = (c_dict.get("med_name"), c_dict.get("chunk_index"))
            if key not in seen_keys:
                seen_keys.add(key)
                collected.append(c_dict)

        async with AsyncSessionLocal() as session:
            if candidates:
                per_med_k = 3 if len(candidates) > 1 else top_k
                for term in candidates:
                    found_in_db = []
                    if query_vector:
                        stmt_med = (
                            select(BulaChunk)
                            .where(BulaChunk.med_name.ilike(f"%{term}%"))
                            .order_by(BulaChunk.embedding.cosine_distance(query_vector))
                            .limit(per_med_k)
                        )
                        res_med = await session.execute(stmt_med)
                        found_in_db = list(res_med.scalars().all())

                    if found_in_db:
                        for chunk in found_in_db:
                            add_chunk_dict(chunk.to_dict())
                            # Se o chunk menciona o título de interações ou contraindicações no fim, puxa o próximo chunk
                            tail = self._strip_accents(chunk.content[-220:]).lower()
                            if "interac" in tail or "contraindic" in tail:
                                stmt_next = select(BulaChunk).where(
                                    BulaChunk.med_name == chunk.med_name,
                                    BulaChunk.chunk_index == chunk.chunk_index + 1,
                                )
                                next_chunk = (await session.execute(stmt_next)).scalar_one_or_none()
                                if next_chunk:
                                    add_chunk_dict(next_chunk.to_dict())
                    else:
                        # Fallback local: lê o PDF em Script/bulario/ sem gastar tokens de embedding
                        local_chunks = self._fallback_chunks_from_local_pdf(
                            term, query, max_chunks=per_med_k
                        )
                        for lc in local_chunks:
                            add_chunk_dict(lc)

            remaining = max(0, top_k - len(collected))
            if remaining > 0 and query_vector:
                stmt_global = (
                    select(BulaChunk)
                    .order_by(BulaChunk.embedding.cosine_distance(query_vector))
                    .limit(top_k + len(seen_keys))
                )
                res_global = await session.execute(stmt_global)
                for chunk in res_global.scalars().all():
                    add_chunk_dict(chunk.to_dict())
                    if len(collected) >= top_k:
                        break

        return collected[: max(top_k, len(collected))]

    async def get_perfil_usuario(self, id_usuario: Optional[UUID]) -> Optional[Dict[str, Any]]:
        if not id_usuario:
            return None

        try:
            async with AsyncSessionLocal() as session:
                res_user = await session.execute(
                    select(UserRegister).where(UserRegister.id_usuario == id_usuario)
                )
                user_reg = res_user.scalar_one_or_none()

                res_farm = await session.execute(
                    select(FarmHistory).where(FarmHistory.user_id == id_usuario)
                )
                farm = res_farm.scalar_one_or_none()

                if not user_reg and not farm:
                    return None

                apelido = user_reg.apelido if user_reg else "Paciente"
                if farm:
                    return farm.to_dict(apelido=apelido)

                return {
                    "idUsuario": str(id_usuario),
                    "apelido": apelido,
                    "idade": None,
                    "peso": None,
                    "altura": None,
                    "imc": None,
                    "gestanteLactante": False,
                    "alergias": None,
                    "problemasSaude": None,
                    "medicacoesContinuas": None,
                    "praticaEsportes": None,
                    "horasSono": None,
                    "atualizadoEm": None,
                }
        except Exception as e:
            logger.error(f"[RAG] Erro ao buscar dados do usuário ({id_usuario}): {e}")
            return None

    async def upsert_perfil_usuario(self, payload: PerfilUsuarioPayload) -> Dict[str, Any]:
        clean_apelido = prompt_service.sanitize_xml(payload.apelido, "Paciente")

        farm_values = {
            "user_id": payload.id_usuario,
            "idade": payload.idade,
            "peso": payload.peso,
            "altura": payload.altura,
            "gestante_lactante": payload.gestante_lactante,
            "alergias": prompt_service.sanitize_xml(payload.alergias, None) if payload.alergias else None,
            "problemas_saude": prompt_service.sanitize_xml(payload.problemas_saude, None) if payload.problemas_saude else None,
            "medicacoes_continuas": prompt_service.sanitize_xml(payload.medicacoes_continuas, None) if payload.medicacoes_continuas else None,
            "pratica_esportes": prompt_service.sanitize_xml(payload.pratica_esportes, None) if payload.pratica_esportes else None,
            "horas_sono": payload.horas_sono,
        }

        async with AsyncSessionLocal() as session:
            stmt_user = pg_insert(UserRegister).values(
                id_usuario=payload.id_usuario,
                apelido=clean_apelido,
            ).on_conflict_do_update(
                index_elements=[UserRegister.id_usuario],
                set_={"apelido": clean_apelido},
            )
            await session.execute(stmt_user)

            stmt_farm = pg_insert(FarmHistory).values(**farm_values)
            update_cols = {k: v for k, v in farm_values.items() if k != "user_id"}
            stmt_farm = stmt_farm.on_conflict_do_update(
                index_elements=[FarmHistory.user_id],
                set_=update_cols,
            )
            await session.execute(stmt_farm)
            await session.commit()

            result = await session.execute(
                select(FarmHistory).where(FarmHistory.user_id == payload.id_usuario)
            )
            farm = result.scalar_one()
            return farm.to_dict(apelido=clean_apelido)

    async def get_historico_consultas(self, id_usuario: UUID) -> List[Dict[str, Any]]:
        try:
            async with AsyncSessionLocal() as session:
                stmt = (
                    select(HistoricoConsultas)
                    .where(HistoricoConsultas.id_usuario == id_usuario)
                    .order_by(desc(HistoricoConsultas.data_hora))
                )
                result = await session.execute(stmt)
                items = result.scalars().all()
                return [item.to_dict() for item in items]
        except Exception as e:
            logger.error(f"[RAG] Erro ao buscar historico_consultas ({id_usuario}): {e}")
            return []

    async def save_historico_consulta(
        self,
        id_usuario: Optional[UUID],
        pergunta_usuario: str,
        resposta_ia: str,
    ) -> None:
        if not id_usuario or not resposta_ia.strip():
            return

        try:
            async with AsyncSessionLocal() as session:
                stmt_user = select(UserRegister).where(UserRegister.id_usuario == id_usuario)
                res_user = await session.execute(stmt_user)
                if not res_user.scalar_one_or_none():
                    session.add(UserRegister(id_usuario=id_usuario, apelido="Paciente"))
                    await session.flush()

                session.add(
                    HistoricoConsultas(
                        id_usuario=id_usuario,
                        pergunta_usuario=prompt_service.sanitize_xml(pergunta_usuario, ""),
                        resposta_ia=resposta_ia,
                    )
                )
                await session.commit()
        except Exception as e:
            logger.error(f"[RAG] Não foi possível salvar no historico_consultas: {e}")


rag_service = RAGService()
