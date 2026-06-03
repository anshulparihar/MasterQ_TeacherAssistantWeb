from pydantic import BaseModel, ConfigDict
from typing import Optional, Dict, Any
import uuid

class ExamTypeBase(BaseModel):
    name: str
    description: Optional[str] = None
    guidelines: Optional[Dict[str, Any]] = None

class ExamTypeCreate(ExamTypeBase):
    pass

class ExamTypeResponse(ExamTypeBase):
    id: uuid.UUID
    
    model_config = ConfigDict(from_attributes=True)
