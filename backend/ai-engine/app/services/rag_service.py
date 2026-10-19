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
from app.services.prompt_service import prompt_service
from app.utils.logger import logger


# Serviço de busca vetorial (RAG) e persistência do usuário, ficha clínica (FarmHistory) e histórico
class RAGService:

    # Remove acentos para compatibilizar a busca ILIKE com o nome limpo das bulas no banco
    @staticmethod
    def _strip_accents(text: str) -> str:
        normalized = unicodedata.normalize("NFKD", text or "")
        return "".join(c for c in normalized if not unicodedata.combining(c))

    # Extrai possíveis nomes de fármacos da pergunta para garantir cobertura em interações
    @classmethod
    def _extract_candidate_terms(cls, query: str, medications: Optional[List[str]] = None) -> List[str]:
        stopwords = {
            "posso", "tomar", "usar", "junto", "juntos", "entre", "interacao", "interacoes",
            "efeito", "efeitos", "colateral", "colaterais", "reacao", "reacoes", "risco",
            "riscos", "bula", "remedio", "remedios", "medicamento", "medicamentos", "comprimido",
            "gotas", "xarope", "para", "serve", "como", "qual", "quais", "quando", "porque",
            "tenho", "estou", "fazer", "causa", "pode", "podem", "deve", "devem", "adulto",
            "crianca", "idoso", "gestante", "gravida", "lactante", "pressao", "diabetes",
            "problema", "problemas", "saude", "alergia", "dose", "dosagem", "posologia"
        }
        candidates: List[str] = []
        for med in (medications or []):
            clean = cls._strip_accents(str(med).strip())
            if len(clean) >= 3 and clean.lower() not in [c.lower() for c in candidates]:
                candidates.append(clean)

        tokens = re.findall(r"[A-Za-zÀ-ÿ]{5,}", query or "")
        for token in tokens:
            clean_token = cls._strip_accents(token)
            low = clean_token.lower()
            if low not in stopwords and low not in [c.lower() for c in candidates]:
                candidates.append(clean_token)
        return candidates[:5]

    # Busca os top_k trechos de bulas mais próximos por distância de cosseno (<=>), equilibrando múltiplos medicamentos
    async def search_relevant_chunks(
        self,
        query: str,
        top_k: int = 4,
        medications: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        meds_clean = [str(m).strip() for m in (medications or []) if m and str(m).strip()]
        enriched_query = f"{', '.join(meds_clean)}: {query}" if meds_clean else query
        query_vector = await embedding_service.get_embedding(
            enriched_query, task_type="RETRIEVAL_QUERY"
        )

        if not query_vector:
            logger.warning(f"Não foi possível gerar embedding para a pergunta: '{query}'")
            return []

        candidates = self._extract_candidate_terms(query, meds_clean)
        collected: List[BulaChunk] = []
        seen_ids = set()

        async with AsyncSessionLocal() as session:
            if candidates:
                per_med_k = 2 if len(candidates) > 1 else top_k
                for term in candidates:
                    stmt_med = (
                        select(BulaChunk)
                        .where(BulaChunk.med_name.ilike(f"%{term}%"))
                        .order_by(BulaChunk.embedding.cosine_distance(query_vector))
                        .limit(per_med_k)
                    )
                    res_med = await session.execute(stmt_med)
                    for chunk in res_med.scalars().all():
                        if chunk.id not in seen_ids:
                            seen_ids.add(chunk.id)
                            collected.append(chunk)

            remaining = max(0, top_k - len(collected))
            if remaining > 0:
                stmt_global = (
                    select(BulaChunk)
                    .order_by(BulaChunk.embedding.cosine_distance(query_vector))
                    .limit(top_k + len(seen_ids))
                )
                res_global = await session.execute(stmt_global)
                for chunk in res_global.scalars().all():
                    if chunk.id not in seen_ids:
                        seen_ids.add(chunk.id)
                        collected.append(chunk)
                        if len(collected) >= top_k:
                            break

            return [chunk.to_dict() for chunk in collected[: max(top_k, len(collected))]]

    # Consulta o registro do usuário (UserRegister) e sua ficha clínica (FarmHistory) pelo UUID
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

    # Salva ou atualiza (Upsert) a ficha clínica em FarmHistory e o apelido em UserRegister
    async def upsert_perfil_usuario(self, payload: PerfilUsuarioPayload) -> Dict[str, Any]:
        clean_apelido = prompt_service.sanitize_xml(payload.apelido, "Visitante")

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
            # Garante que o usuário exista na tabela user_register antes de gravar em farm_history
            stmt_user = pg_insert(UserRegister).values(
                id_usuario=payload.id_usuario,
                apelido=clean_apelido,
            ).on_conflict_do_update(
                index_elements=[UserRegister.id_usuario],
                set_={"apelido": clean_apelido},
            )
            await session.execute(stmt_user)

            # Faz Upsert da ficha clínica na tabela farm_history
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

    # Lista as consultas anteriores vinculadas ao UUID
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

    # Registra a pergunta e a resposta da IA na tabela 'historico_consultas'
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
                    session.add(UserRegister(id_usuario=id_usuario, apelido="Visitante"))
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
