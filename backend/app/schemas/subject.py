from pydantic import BaseModel, ConfigDict
from typing import Optional
import uuid

class SubjectBase(BaseModel):
    name: str
    description: Optional[str] = None

class SubjectCreate(SubjectBase):
    pass

class SubjectResponse(SubjectBase):
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
