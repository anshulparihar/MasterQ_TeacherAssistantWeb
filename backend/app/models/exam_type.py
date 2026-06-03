import uuid
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class ExamType(Base):
    __tablename__ = "exam_types"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    guidelines: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    few_shot_examples: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    question_papers = relationship("QuestionPaper", back_populates="exam_type")
