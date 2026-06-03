import uuid
from sqlalchemy import String, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base

class Topic(Base):
    __tablename__ = "topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    subject = relationship("Subject", back_populates="topics")
    questions = relationship("Question", back_populates="topic")

from sqlalchemy import JSON, Float

class DocumentTopic(Base):
    __tablename__ = "document_topics"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    topic_name: Mapped[str] = mapped_column(String(255), nullable=False)
    subtopics: Mapped[list[str]] = mapped_column(JSON, default=list)
    importance_score: Mapped[float] = mapped_column(Float, default=0.5)

    document = relationship("Document")
