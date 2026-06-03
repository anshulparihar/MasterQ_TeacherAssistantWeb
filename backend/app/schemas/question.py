from pydantic import BaseModel, ConfigDict, Field, computed_field, model_validator
from typing import Optional, List, Dict
from datetime import datetime
import uuid

class QuestionGenerationRequest(BaseModel):
    subject_id: uuid.UUID
    academic_level: str
    exam_type_id: uuid.UUID
    
    mcq_easy:      int = Field(0, ge=0, description="Easy MCQ count")
    mcq_medium:    int = Field(0, ge=0, description="Medium MCQ count")
    mcq_hard:      int = Field(0, ge=0, description="Hard MCQ count")
    theory_easy:   int = Field(0, ge=0, description="Easy theory count")
    theory_medium: int = Field(0, ge=0, description="Medium theory count")
    theory_hard:   int = Field(0, ge=0, description="Hard theory count")

    selected_document_ids: List[uuid.UUID] = []
    from_this_only: bool = False
    topics: List[str] = []
    selected_topics: List[str] = []
    selected_subtopics: List[str] = []

    @computed_field
    @property
    def mcq_count(self) -> int:
        return self.mcq_easy + self.mcq_medium + self.mcq_hard

    @computed_field
    @property
    def theory_count(self) -> int:
        return self.theory_easy + self.theory_medium + self.theory_hard

    @model_validator(mode='after')
    def validate_totals(self):
        total = self.mcq_count + self.theory_count
        if total == 0:
            raise ValueError(
                "At least one question must be requested across any type and difficulty."
            )
        if total > 100:
            raise ValueError(
                f"Total questions ({total}) exceeds the maximum of 100 per generation."
            )
        return self

class QuestionBase(BaseModel):
    text: str
    type: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    model_answer: Optional[str] = None
    difficulty: str
    topic_id: uuid.UUID

class QuestionResponse(QuestionBase):
    id: uuid.UUID
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)

class QuestionPaperResponse(BaseModel):
    id: uuid.UUID
    title: str
    user_id: uuid.UUID
    subject_id: uuid.UUID
    exam_type_id: uuid.UUID
    created_at: datetime
    questions: List[QuestionResponse] = []
    
    model_config = ConfigDict(from_attributes=True)
