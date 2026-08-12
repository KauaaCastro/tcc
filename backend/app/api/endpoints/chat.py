from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.ai_service import ai_service
from app.utils.logger import logger

router = APIRouter()

@router.post("/chat", response_model=ChatResponse, tags=["Chat"])
async def chat_endpoint(request: ChatRequest):
    """
    Endpoint síncrono/padrão de consulta de farmacologia e medicamentos.
    Retorna resposta em JSON completo com alert_type para a UI.
    """
    try:
        result = await ai_service.generate_response(
            message=request.message,
            profile_type=request.profile_type
        )
        return ChatResponse(
            answer=result["answer"],
            alert_type=result["alert_type"],
            profile_type=result["profile_type"],
            trusted_sources=result.get("trusted_sources")
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao processar consulta médica.")

@router.post("/chat/stream", tags=["Chat"])
async def chat_stream_endpoint(request: ChatRequest):
    """
    Endpoint em streaming SSE (Server-Sent Events) para envio token a token à UI.
    """
    try:
        generator = ai_service.generate_streaming_response(
            message=request.message,
            profile_type=request.profile_type
        )
        return StreamingResponse(
            generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"
            }
        )
    except Exception as e:
        logger.error(f"Error in chat stream endpoint: {str(e)}")
        raise HTTPException(status_code=500, detail="Erro interno ao iniciar streaming.")
