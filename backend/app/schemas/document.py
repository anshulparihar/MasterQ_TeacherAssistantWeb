from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime
import uuid

class DocumentBase(BaseModel):
    filename: str
    doc_type: str

class DocumentCreate(DocumentBase):
    s3_key: str

class DocumentResponse(DocumentBase):
    id: uuid.UUID
    user_id: Optional[uuid.UUID] = None
    s3_key: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class DocumentList(BaseModel):
    documents: list[DocumentResponse]
