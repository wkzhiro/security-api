from pydantic import BaseModel
from typing import Optional
from datetime import datetime

class ChatRequest(BaseModel):
    message: str
    user_email: str

class ChatResponse(BaseModel):
    response: str
    success: bool = True

class ConversationRecord(BaseModel):
    id: Optional[str] = None
    session_id: str
    user_email: str
    message: str
    response: str
    timestamp: datetime = datetime.now()

class ChatSession(BaseModel):
    id: Optional[int] = None
    user_email: str
    session_id: str
    created_at: Optional[datetime] = None