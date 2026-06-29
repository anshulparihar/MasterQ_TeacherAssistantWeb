import uuid
import sqlalchemy
from sqlalchemy import String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Subject(Base):
    __tablename__ = "subjects"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    academic_levels: Mapped[list[str] | None] = mapped_column(sqlalchemy.dialects.postgresql.JSONB, nullable=True)

    topics = relationship("Topic", back_populates="subject")
    question_papers = relationship("QuestionPaper", back_populates="subject")
