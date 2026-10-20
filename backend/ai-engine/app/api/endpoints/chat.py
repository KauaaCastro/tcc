import json
from uuid import UUID
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.schemas.chat import (
    QueryRequest,
    QueryResponse,
    PerfilUsuarioPayload,
    AlertType,
    OfficialLink,
)
from app.services.guardrail_service import guardrail_service
from app.services.rag_service import rag_service
from app.services.prompt_service import prompt_service
from app.services.llm_service import llm_service, LLMUnavailableError
from app.utils.logger import logger

router = APIRouter()

OFFICIAL_FALLBACK_LINKS = [
    {"name": "Bulário Eletrônico da ANVISA", "url": "https://consultas.anvisa.gov.br/#/bulario/"},
    {"name": "Medscape Drug Interaction Checker", "url": "https://reference.medscape.com/drug-interactionchecker"},
]

FALLBACK_MESSAGE = (
    "O serviço de Inteligência Artificial está temporariamente indisponível.\n"
    "Consulte diretamente as fontes oficiais:\n"
    "• Bulário Eletrônico da ANVISA: https://consultas.anvisa.gov.br/#/bulario/\n"
    "• Medscape Drug Interaction Checker: https://reference.medscape.com/drug-interactionchecker"
)


async def chat_stream_generator(request: QueryRequest):
    clean_question = prompt_service.sanitize_xml(request.question, "")
    is_valid, block_reason, alert = guardrail_service.validate_scope(clean_question, request.medications)
    if not is_valid:
        payload = {
            "chunk": block_reason,
            "alert_type": alert.value if alert else AlertType.INFO.value,
            "sources": [],
            "links": [],
            "is_final": True,
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        return

    logger.info(
        f"[CHAT] Consulta RAG: '{clean_question[:60]}...' | UUID: {request.id_usuario} | Perfil: {request.profile.value}"
    )
    perfil_data = await rag_service.get_perfil_usuario(request.id_usuario)
    retrieved_chunks = await rag_service.search_relevant_chunks(
        clean_question, top_k=6, medications=request.medications
    )
    sources_list = [
        f"{c.get('med_name', 'Bula')} - Chunk #{c.get('chunk_index', i)}"
        for i, c in enumerate(retrieved_chunks, start=1)
    ]

    sandwich_prompt = prompt_service.build_sandwich_prompt(
        question=clean_question,
        retrieved_chunks=retrieved_chunks,
        perfil_data=perfil_data,
        profile=request.profile,
        medications=request.medications,
    )

    raw_parts = []
    header_buffer = ""
    header_cleaned = False

    try:
        async for text_chunk in llm_service.generate_response_stream(sandwich_prompt, clean_question):
            raw_parts.append(text_chunk)

            # Remove a tag interna ([DANGER]/[WARNING]/[INFO]) do início antes de exibir ao usuário
            if not header_cleaned:
                header_buffer += text_chunk
                if len(header_buffer) < 24 and "\n" not in header_buffer:
                    continue
                header_cleaned = True
                clean_chunk = prompt_service.clean_response_tags(header_buffer)
                if not clean_chunk:
                    continue
            else:
                clean_chunk = text_chunk

            payload = {
                "chunk": clean_chunk,
                "alert_type": None,
                "sources": [],
                "links": [],
                "is_final": False,
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        if not header_cleaned and header_buffer:
            clean_chunk = prompt_service.clean_response_tags(header_buffer)
            if clean_chunk:
                yield f"data: {json.dumps({'chunk': clean_chunk, 'alert_type': None, 'sources': [], 'links': [], 'is_final': False}, ensure_ascii=False)}\n\n"

        full_raw_answer = "".join(raw_parts).strip()
        detected_alert = prompt_service.detect_alert_type(full_raw_answer)
        clean_full_answer = prompt_service.clean_response_tags(full_raw_answer).strip()

        if request.id_usuario and clean_full_answer:
            await rag_service.save_historico_consulta(
                id_usuario=request.id_usuario,
                pergunta_usuario=clean_question,
                resposta_ia=clean_full_answer,
            )

        final_payload = {
            "chunk": "",
            "alert_type": detected_alert.value,
            "sources": sources_list,
            "links": [],
            "is_final": True,
        }
        yield f"data: {json.dumps(final_payload, ensure_ascii=False)}\n\n"

    except (LLMUnavailableError, Exception) as e:
        logger.error(f"[CHAT] Fallback Seguro ativado durante streaming: {str(e)}")
        error_payload = {
            "chunk": f"\n\n{FALLBACK_MESSAGE}" if raw_parts else FALLBACK_MESSAGE,
            "alert_type": AlertType.RESTRICTION.value,
            "sources": sources_list,
            "links": OFFICIAL_FALLBACK_LINKS,
            "is_final": True,
        }
        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"


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


@router.post("/ai/query", response_model=QueryResponse, summary="Consulta Farmacêutica via RAG (JSON)")
async def ai_query_endpoint(request: QueryRequest):
    clean_question = prompt_service.sanitize_xml(request.question, "")
    is_valid, block_reason, alert = guardrail_service.validate_scope(clean_question, request.medications)
    if not is_valid:
        resolved_alert = alert if alert else AlertType.INFO
        return QueryResponse(
            response=block_reason,
            sources=[],
            severity=resolved_alert,
            alert_type=resolved_alert,
            links=[],
        )

    perfil_data = await rag_service.get_perfil_usuario(request.id_usuario)
    retrieved_chunks = await rag_service.search_relevant_chunks(
        clean_question, top_k=6, medications=request.medications
    )
    sources_list = [
        f"{c.get('med_name', 'Bula')} - Chunk #{c.get('chunk_index', i)}"
        for i, c in enumerate(retrieved_chunks, start=1)
    ]

    sandwich_prompt = prompt_service.build_sandwich_prompt(
        question=clean_question,
        retrieved_chunks=retrieved_chunks,
        perfil_data=perfil_data,
        profile=request.profile,
        medications=request.medications,
    )

    try:
        raw_answer = await llm_service.generate_response(sandwich_prompt, clean_question)
    except (LLMUnavailableError, Exception) as e:
        logger.error(f"[CHAT] Fallback Seguro ativado em /ai/query: {str(e)}")
        return QueryResponse(
            response=FALLBACK_MESSAGE,
            sources=sources_list,
            severity=AlertType.RESTRICTION,
            alert_type=AlertType.RESTRICTION,
            links=[OfficialLink(**link) for link in OFFICIAL_FALLBACK_LINKS],
        )

    detected_alert = prompt_service.detect_alert_type(raw_answer)
    clean_answer = prompt_service.clean_response_tags(raw_answer).strip()

    if request.id_usuario and clean_answer:
        await rag_service.save_historico_consulta(
            id_usuario=request.id_usuario,
            pergunta_usuario=clean_question,
            resposta_ia=clean_answer,
        )

    return QueryResponse(
        response=clean_answer,
        sources=sources_list,
        severity=detected_alert,
        alert_type=detected_alert,
        links=[],
    )


@router.post("/perfil", summary="Salvar ou Atualizar Perfil Clínico Anônimo")
async def salvar_perfil_endpoint(payload: PerfilUsuarioPayload):
    perfil_salvo = await rag_service.upsert_perfil_usuario(payload)
    return {
        "mensagem": "Perfil clínico salvo com sucesso.",
        "perfil": perfil_salvo,
    }


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
