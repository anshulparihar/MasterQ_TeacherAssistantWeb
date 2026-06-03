import uuid
from datetime import datetime
from sqlalchemy import String, Text, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from pgvector.sqlalchemy import Vector
from app.database import Base

class Question(Base):
    __tablename__ = "questions"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    text: Mapped[str] = mapped_column(Text, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False) # 'mcq' or 'theory'
    options: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    correct_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    model_answer: Mapped[str | None] = mapped_column(Text, nullable=True)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)
    topic_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("topics.id", ondelete="CASCADE"), nullable=True)
    question_paper_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("question_papers.id", ondelete="SET NULL"), nullable=True)
    question_embedding = mapped_column(Vector(768))
    question_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)
    diagram_url: Mapped[str | None] = mapped_column(String(1024), nullable=True)
    diagram_type: Mapped[str | None] = mapped_column(String(50), nullable=True)
    explanation: Mapped[str | None] = mapped_column(Text, nullable=True)
    hint: Mapped[str | None] = mapped_column(Text, nullable=True)
    marks: Mapped[float | None] = mapped_column(nullable=True)
    is_recommendation: Mapped[bool] = mapped_column(default=False, server_default="false")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    topic = relationship("Topic", back_populates="questions")
    question_paper = relationship("QuestionPaper", back_populates="questions")

class QuestionPaper(Base):
    __tablename__ = "question_papers"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    subject_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False)
    exam_type_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("exam_types.id", ondelete="CASCADE"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=datetime.utcnow)

    user = relationship("User", back_populates="question_papers")
    subject = relationship("Subject", back_populates="question_papers")
    exam_type = relationship("ExamType", back_populates="question_papers")
    questions = relationship("Question", back_populates="question_paper")
    paper_documents = relationship("PaperDocument", back_populates="question_paper", cascade="all, delete-orphan")

class PaperDocument(Base):
    __tablename__ = "paper_documents"

    question_paper_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("question_papers.id", ondelete="CASCADE"), primary_key=True)
    document_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("documents.id", ondelete="CASCADE"), primary_key=True)

    question_paper = relationship("QuestionPaper", back_populates="paper_documents")
    document = relationship("Document", back_populates="paper_documents")
