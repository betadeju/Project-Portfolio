from fastapi import APIRouter, HTTPException
from app.models.chat import ChatRequest, ChatResponse
from app.services.ai_service  import ai_service
from datetime import datetime
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        if not request.message:
            raise HTTPException(status_code=400, detail="Message is required")
        logger.info(f"Received chat request: {request.message[:50]}...")  # Log only the first 50 characters for brevity
        ai_response = ai_service.generate_reponse(
                request.message,
                request.conversation_history or []
                )
        return ChatResponse(
            response=ai_response,
            success=True,
            timestamp=datetime.utcnow().isoformat()
        )
    except HTTPException as e:
        
        raise 
    except Exception as e:
        logger.error(f"Error processing chat request: {str(e)}")
        return ChatResponse(
            response="An error occurred while processing your request.",
            success=False,
            timestamp=datetime.utcnow().isoformat()
        )
@router.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": datetime.utcnow().isoformat()}