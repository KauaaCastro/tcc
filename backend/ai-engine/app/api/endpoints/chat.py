import json
from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    QueryRequest,
    QueryResponse,
    PerfilUsuarioPayload,
    AlertType,
)
from app.services.guardrail_service import guardrail_service
from app.services.rag_service import rag_service
from app.services.prompt_service import prompt_service
from app.services.llm_service import llm_service
from app.utils.logger import logger

router = APIRouter()


# Orquestra Guardrail, busca de perfil (UUID), RAG, Prompt Sanduíche e streaming SSE
async def chat_stream_generator(request: QueryRequest):
    clean_question = prompt_service.sanitize_xml(request.question, "")
    is_valid, block_reason, alert = guardrail_service.validate_scope(clean_question)
    if not is_valid:
        payload = {
            "chunk": block_reason,
            "alert_type": alert.value if alert else AlertType.INFO.value,
            "is_final": True,
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        return

    logger.info(
        f"[CHAT] Consulta RAG: '{clean_question[:60]}...' | UUID: {request.id_usuario} | Perfil: {request.profile.value}"
    )
    perfil_data = await rag_service.get_perfil_usuario(request.id_usuario)
    retrieved_chunks = await rag_service.search_relevant_chunks(clean_question, top_k=4)

    sandwich_prompt = prompt_service.build_sandwich_prompt(
        question=clean_question,
        retrieved_chunks=retrieved_chunks,
        perfil_data=perfil_data,
        profile=request.profile,
    )

    full_response_parts = []
    try:
        async for text_chunk in llm_service.generate_response_stream(sandwich_prompt, clean_question):
            full_response_parts.append(text_chunk)
            payload = {
                "chunk": text_chunk,
                "alert_type": None,
                "is_final": False,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # Grava a consulta no histórico se houver UUID informado
        full_answer = "".join(full_response_parts).strip()
        if request.id_usuario and full_answer:
            await rag_service.save_historico_consulta(
                id_usuario=request.id_usuario,
                pergunta_usuario=clean_question,
                resposta_ia=full_answer,
            )

        final_payload = {
            "chunk": "",
            "alert_type": None,
            "is_final": True,
        }
        yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.error(f"[CHAT] Erro durante o streaming de IA: {str(e)}")
        error_payload = {
            "chunk": (
                "\n\n[AVISO DE SEGURANÇA CLÍNICA - FALLBACK ATIVADO]\n"
                "O serviço de Inteligência Artificial está temporariamente indisponível.\n"
                "Para garantir sua segurança sem risco de alucinações, consulte diretamente as fontes oficiais:\n"
                "• Bulário Eletrônico da ANVISA: https://consultas.anvisa.gov.br/#/bulario/\n"
                "• Medscape Drug Interaction Checker: https://reference.medscape.com/drug-interactionchecker"
            ),
            "alert_type": AlertType.RESTRICTION.value,
            "links": [
                {"name": "Bulário Eletrônico da ANVISA", "url": "https://consultas.anvisa.gov.br/#/bulario/"},
                {"name": "Medscape Drug Interaction Checker", "url": "https://reference.medscape.com/drug-interactionchecker"},
            ],
            "is_final": True,
        }
        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"


# Rota de consulta clínica com transmissão em tempo real (SSE)
@router.post("/chat/stream", summary="Consulta clínica com streaming SSE")
async def chat_stream_endpoint(request: QueryRequest):
    return StreamingResponse(
        chat_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# Rota de consulta farmacêutica via RAG retornando JSON completo
@router.post("/ai/query", response_model=QueryResponse, summary="Consulta Farmacêutica via RAG (JSON)")
async def ai_query_endpoint(request: QueryRequest):
    clean_question = prompt_service.sanitize_xml(request.question, "")
    is_valid, block_reason, alert = guardrail_service.validate_scope(clean_question)
    if not is_valid:
        return QueryResponse(
            response=block_reason,
            sources=[],
            severity=alert if alert else AlertType.INFO,
        )

    perfil_data = await rag_service.get_perfil_usuario(request.id_usuario)
    retrieved_chunks = await rag_service.search_relevant_chunks(clean_question, top_k=4)

    sandwich_prompt = prompt_service.build_sandwich_prompt(
        question=clean_question,
        retrieved_chunks=retrieved_chunks,
        perfil_data=perfil_data,
        profile=request.profile,
    )

    answer = await llm_service.generate_response(sandwich_prompt, clean_question)
    if not answer:
        return QueryResponse(
            response=(
                "[AVISO DE SEGURANÇA CLÍNICA - FALLBACK ATIVADO] "
                "Serviço de IA temporariamente indisponível. Consulte o Bulário Eletrônico da ANVISA."
            ),
            sources=[],
            severity=AlertType.RESTRICTION,
        )

    if request.id_usuario:
        await rag_service.save_historico_consulta(
            id_usuario=request.id_usuario,
            pergunta_usuario=clean_question,
            resposta_ia=answer,
        )

    sources_list = [
        f"{c.get('med_name', 'Bula')} - Chunk #{c.get('chunk_index', i)}"
        for i, c in enumerate(retrieved_chunks, start=1)
    ]

    return QueryResponse(
        response=answer,
        sources=sources_list,
        severity=AlertType.INFO,
    )


# Salva ou atualiza o Perfil Clínico Anônimo (Upsert por UUID)
@router.post("/perfil", summary="Salvar ou Atualizar Perfil Clínico Anônimo")
async def salvar_perfil_endpoint(payload: PerfilUsuarioPayload):
    perfil_salvo = await rag_service.upsert_perfil_usuario(payload)
    return {
        "mensagem": "Perfil clínico anônimo salvo com sucesso.",
        "perfil": perfil_salvo,
    }


# Carrega o Perfil Clínico Anônimo e o histórico de consultas pelo UUID
@router.get("/perfil/{id_usuario}", summary="Carregar Perfil Clínico Anônimo e Histórico")
async def carregar_perfil_endpoint(id_usuario: UUID):
    perfil = await rag_service.get_perfil_usuario(id_usuario)
    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado para este UUID.")

    historico = await rag_service.get_historico_consultas(id_usuario)
    return {
        "perfil": perfil,
        "historico": historico,
    }
