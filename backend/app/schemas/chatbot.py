from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime
import uuid

class ChatMessageRequest(BaseModel):
    session_id: uuid.UUID
    content: str

class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    references: Optional[List[str]] = None
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class ChatSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
