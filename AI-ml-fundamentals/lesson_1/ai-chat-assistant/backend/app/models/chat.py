#Why Pydantic? It automatically validates data and 
#converts types—essential for reliable AI systems that handle unpredictable user input.

from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str
    conversation_history: Optional[List[ChatMessage]] = []

class ChatResponse(BaseModel):
    response: str
    success : bool
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None