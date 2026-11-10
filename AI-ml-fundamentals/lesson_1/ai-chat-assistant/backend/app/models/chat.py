#Why Pydantic? It automatically validates data and 
#converts types—essential for reliable AI systems that handle unpredictable user input.

from pydantic import BaseModel,Field, field_validator
from typing import List, Optional
from datetime import datetime

class ChatMessage(BaseModel):
    role: str   # "user" or "assistant"
    content: str
    timestamp: Optional[datetime] = None

class ChatRequest(BaseModel):
    message: str = Field(..., max_length=2000)
    conversation_history: Optional[List[ChatMessage]] = []
    @field_validator("message")
    @classmethod
    def message_must_not_be_blank(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Message cannot be empty")
        return value

class ChatResponse(BaseModel):
    response: str
    success : bool
    error_message: Optional[str] = None
    timestamp: Optional[datetime] = None