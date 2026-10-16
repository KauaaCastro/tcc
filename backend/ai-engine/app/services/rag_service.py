from typing import List, Dict, Any, Optional
from uuid import UUID
from sqlalchemy import select, desc
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.session import AsyncSessionLocal
from app.db.models import BulaChunk, PerfilUsuario, HistoricoConsultas
from app.schemas.chat import PerfilUsuarioPayload
from app.services.embedding_service import embedding_service
from app.services.prompt_service import prompt_service
from app.utils.logger import logger


# Serviço de busca vetorial (RAG) e persistência do perfil anônimo e histórico
class RAGService:

    # Busca os top_k trechos de bulas mais próximos por distância de cosseno (<=>)
    async def search_relevant_chunks(
        self,
        query: str,
        top_k: int = 4
    ) -> List[Dict[str, Any]]:
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
            return [chunk.to_dict() for chunk in chunks]

    # Consulta o perfil clínico anônimo pelo UUID v4
    async def get_perfil_usuario(self, id_usuario: Optional[UUID]) -> Optional[Dict[str, Any]]:
        if not id_usuario:
            return None

        try:
            async with AsyncSessionLocal() as session:
                stmt = select(PerfilUsuario).where(PerfilUsuario.id_usuario == id_usuario)
                result = await session.execute(stmt)
                perfil = result.scalar_one_or_none()
                return perfil.to_dict() if perfil else None
        except Exception as e:
            logger.error(f"[RAG] Erro ao buscar perfil_usuario ({id_usuario}): {e}")
            return None

    # Salva ou atualiza (Upsert) o perfil clínico anônimo limpando tags XML
    async def upsert_perfil_usuario(self, payload: PerfilUsuarioPayload) -> Dict[str, Any]:
        values = {
            "id_usuario": payload.id_usuario,
            "apelido": prompt_service.sanitize_xml(payload.apelido, "Visitante"),
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
            stmt = pg_insert(PerfilUsuario).values(**values)
            update_cols = {k: v for k, v in values.items() if k != "id_usuario"}
            stmt = stmt.on_conflict_do_update(
                index_elements=[PerfilUsuario.id_usuario],
                set_=update_cols,
            )
            await session.execute(stmt)
            await session.commit()

            result = await session.execute(
                select(PerfilUsuario).where(PerfilUsuario.id_usuario == payload.id_usuario)
            )
            perfil = result.scalar_one()
            return perfil.to_dict()

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
                stmt_perfil = select(PerfilUsuario).where(PerfilUsuario.id_usuario == id_usuario)
                res_perfil = await session.execute(stmt_perfil)
                if not res_perfil.scalar_one_or_none():
                    session.add(PerfilUsuario(id_usuario=id_usuario, apelido="Visitante"))
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
