import json
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.schemas.chat import QueryRequest, AlertType
from app.services.guardrail_service import guardrail_service
from app.services.rag_service import rag_service
from app.services.prompt_service import prompt_service
from app.services.llm_service import llm_service
from app.utils.logger import logger

router = APIRouter()


async def chat_stream_generator(request: QueryRequest):
    """
    Gerador do pipeline RAG que orquestra Guardrails, busca vetorial e streaming LLM.
    """
    # -------------------------------------------------------------
    # 1. Guardrail: Validação prévia de escopo médico/farmacológico
    # -------------------------------------------------------------
    is_valid, block_reason, alert = guardrail_service.validate_scope(request.question)
    if not is_valid:
        payload = {
            "chunk": block_reason,
            "alert_type": alert.value if alert else AlertType.INFO.value,
            "is_final": True
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        return

    # -------------------------------------------------------------
    # 2. RAG: Busca semântica dos chunks da ANVISA no PGVector
    # -------------------------------------------------------------
    logger.info(f"[CHAT] Iniciando busca RAG para: '{request.question[:60]}...' | Perfil: {request.profile.value}")
    retrieved_chunks = await rag_service.search_relevant_chunks(request.question, top_k=4)

    # -------------------------------------------------------------
    # 3. Prompt: Montagem adaptativa baseada nos templates externos
    # -------------------------------------------------------------
    system_prompt = prompt_service.build_system_prompt(request.profile, retrieved_chunks)

    # -------------------------------------------------------------
    # 4. LLM: Transmissão em tempo real via Server-Sent Events (SSE)
    # -------------------------------------------------------------
    try:
        async for text_chunk in llm_service.generate_response_stream(system_prompt, request.question):
            payload = {
                "chunk": text_chunk,
                "alert_type": None,
                "is_final": False
            }
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        # Mensagem de encerramento do stream
        final_payload = {
            "chunk": "",
            "alert_type": None,
            "is_final": True
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
                {"name": "Medscape Drug Interaction Checker", "url": "https://reference.medscape.com/drug-interactionchecker"}
            ],
            "is_final": True
        }
        yield f"data: {json.dumps(error_payload, ensure_ascii=False)}\n\n"


@router.post("/chat/stream", summary="Consulta clínica com streaming SSE e RAG")
async def chat_stream_endpoint(request: QueryRequest):
    """
    Endpoint principal de interação medicamentosa.
    Retorna Server-Sent Events (SSE) transmitindo o laudo clínico em tempo real.
    """
    return StreamingResponse(
        chat_stream_generator(request),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",  # Desativa buffering no proxy Nginx
        }
    )
