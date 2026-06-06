import asyncio
import json
import uuid
import time
import structlog
import google.generativeai as genai

from app.config import settings
from app.models.document import Document, DocumentChunk
from app.services.storage_service import storage_service
from app.services.document_parser import parse_document
from app.services.chunking_service import chunk_text
from app.services.embedding_service import embedding_service
from app.services.topic_service import topic_service
from app.workers.celery_app import celery_app
from sqlalchemy.future import select
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

logger = structlog.get_logger()

genai.configure(api_key=settings.GEMINI_API_KEY)
_gemini_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)


def _make_session_factory():
    """
    Creates a brand-new AsyncEngine and session factory.

    MUST be called inside the task, never at module level.
    Celery uses ForkPoolWorker: the parent process imports this module and
    creates the engine. Each fork inherits the parent's engine whose asyncpg
    connection pool is bound to the parent's event loop. asyncio.run() in
    the child creates a NEW event loop, so any Future from the inherited
    engine raises 'Future attached to a different loop'.

    Creating a fresh engine per-task avoids this entirely.
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=False,
        future=True,
        pool_pre_ping=True,
        # Small pool — each Celery task is short-lived, no need for persistence
        pool_size=2,
        max_overflow=0,
    )
    SessionLocal = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
        autoflush=False,
    )
    return engine, SessionLocal


async def _auto_detect_subject_and_level(
    db,
    text_content: str
) -> tuple[uuid.UUID | None, str | None]:
    """
    Uses Gemini to automatically determine:
    1. Which subject (from the DB subjects table) this document belongs to.
    2. What academic level the content is written for.

    Returns (subject_id_uuid, academic_level_string) or (None, None) on failure.
    """
    # 1. Fetch all available subjects from DB
    subj_result = await db.execute(text("SELECT id, name FROM subjects ORDER BY name ASC"))
    subjects = subj_result.all()  # list of (id, name) rows

    if not subjects:
        logger.warning("auto_detect_subject: no subjects found in DB, skipping detection")
        return None, None

    subject_list_str = "\n".join([f'- "{row[1]}"' for row in subjects])

    # 2. Use first 8000 chars — enough for Gemini to identify the subject clearly
    sample_text = text_content[:8000]

    prompt = f"""You are a subject classification assistant for an educational platform.

Below is the beginning of an educational document. Your job is to:
1. Identify which subject from the provided list this document belongs to.
2. Identify the academic level of this content.

AVAILABLE SUBJECTS (choose EXACTLY one name from this list, or null if none match):
{subject_list_str}

ACADEMIC LEVEL OPTIONS (choose EXACTLY one):
- "Primary" (Grade 1-5)
- "Middle School" (Grade 6-8)
- "High School" (Grade 9-12)
- "Undergraduate" (College/University)
- "Postgraduate" (Masters/PhD)
- "Professional" (Competitive exams, certifications)

DOCUMENT SAMPLE:
{sample_text}

Return ONLY a valid JSON object. No explanation. No markdown:
{{
  "subject_name": "<exact name from list above, or null if none match>",
  "academic_level": "<one of the exact level strings above>",
  "confidence": 0.95
}}"""

    try:
        response = await asyncio.to_thread(
            _gemini_model.generate_content,
            prompt,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        data = json.loads(response.text)

        detected_subject_name = data.get("subject_name")
        detected_level = data.get("academic_level")
        confidence = float(data.get("confidence", 0.0))

        logger.info(
            "auto_detect_subject_result",
            detected_subject=detected_subject_name,
            detected_level=detected_level,
            confidence=confidence
        )

        # 3. Match detected name back to a real subject UUID (case-insensitive)
        matched_id = None
        if detected_subject_name:
            for row in subjects:
                if row[1].strip().lower() == detected_subject_name.strip().lower():
                    matched_id = row[0]  # UUID from DB
                    break

        if not matched_id:
            logger.warning(
                "auto_detect_subject: detected subject name not matched in DB",
                detected=detected_subject_name
            )

        return matched_id, detected_level

    except Exception as e:
        logger.error("auto_detect_subject_failed", error=str(e))
        return None, None


async def _process_document_async(document_id: str):
    logger.info("starting_document_processing", document_id=document_id)
    start_time = time.time()

    # Create a fresh engine per task — avoids 'Future attached to a different loop'
    # error that occurs when the module-level engine is shared across Celery fork workers.
    engine, SessionLocal = _make_session_factory()

    try:
        async with SessionLocal() as db:
            # 1. Fetch document from DB
            doc_uuid = uuid.UUID(document_id)
            result = await db.execute(select(Document).where(Document.id == doc_uuid))
            document = result.scalars().first()

            if not document:
                logger.error("document_not_found_in_db", document_id=document_id)
                return

            try:
                # 2. Download file from MinIO
                bucket = settings.MINIO_BUCKET_ADMIN if document.doc_type == 'admin' else settings.MINIO_BUCKET_USER
                file_bytes = storage_service.download_file(bucket, document.s3_key)

                # Determine mime type from extension
                ext = document.filename.split('.')[-1].lower()
                mime_type = 'application/octet-stream'
                if ext == 'pdf':
                    mime_type = 'application/pdf'
                elif ext == 'docx':
                    mime_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                elif ext in ['txt', 'md']:
                    mime_type = 'text/plain'

                # 3. Parse document text
                parsed_result = await parse_document(file_bytes, mime_type)
                text_content = parsed_result.get("text", "") if isinstance(parsed_result, dict) else parsed_result

                # 4. Auto-detect subject and academic level if not already set by the user
                if not document.subject_id:
                    logger.info("auto_detecting_subject", document_id=document_id)
                    detected_subject_id, detected_level = await _auto_detect_subject_and_level(db, text_content)
                    logger.info(f'---- Detected subject and level: {detected_subject_id}, {detected_level} -----')
                    if detected_subject_id:
                        document.subject_id = detected_subject_id
                        logger.info(
                            "subject_auto_assigned",
                            document_id=document_id,
                            subject_id=str(detected_subject_id)
                        )
                    if detected_level:
                        document.academic_level = detected_level
                        logger.info(
                            "academic_level_auto_assigned",
                            document_id=document_id,
                            academic_level=detected_level
                        )
                else:
                    logger.info(
                        "subject_already_set_skipping_detection",
                        document_id=document_id,
                        subject_id=str(document.subject_id)
                    )

                # 5. Chunk text
                chunks = chunk_text(text_content, chunk_size=settings.CHUNK_SIZE, overlap=settings.CHUNK_OVERLAP)

                if chunks:
                    texts_to_embed = [c['content'] for c in chunks]

                    # 6. Generate embeddings in batches
                    embeddings = await embedding_service.embed_texts(texts_to_embed)

                    # 7. Store chunks with embeddings in document_chunks
                    db_chunks = []
                    for chunk, embedding in zip(chunks, embeddings):
                        db_chunk = DocumentChunk(
                            document_id=doc_uuid,
                            content=chunk['content'],
                            page_number=chunk['metadata']['approximate_page'],
                            embedding=embedding
                        )
                        db_chunks.append(db_chunk)

                    db.add_all(db_chunks)

                # 8. Extract topics — subject_name is now reliably set from step 4
                subject_name = None
                if document.subject_id:
                    sub_result = await db.execute(
                        text("SELECT name FROM subjects WHERE id = :id"),
                        {"id": str(document.subject_id)}
                    )
                    sub_row = sub_result.first()
                    if sub_row:
                        subject_name = sub_row[0]

                await topic_service.extract_topics_from_document(
                    db=db,
                    document_id=doc_uuid,
                    document_text=text_content,
                    subject_name=subject_name
                )

                # 9. Mark document ready and commit everything
                document.status = 'ready'
                document.chunk_count = len(chunks)
                await db.commit()

                duration_sec = time.time() - start_time
                logger.info(
                    "document_ingested",
                    document_id=document_id,
                    chunk_count=len(chunks),
                    subject_id=str(document.subject_id) if document.subject_id else None,
                    academic_level=document.academic_level,
                    duration_sec=round(duration_sec, 2)
                )

            except Exception as e:
                duration_sec = time.time() - start_time
                logger.error(
                    "document_ingestion_failed",
                    document_id=document_id,
                    duration_sec=round(duration_sec, 2),
                    error=str(e)
                )
                document.status = 'failed'
                await db.commit()
                raise

    finally:
        # Always dispose the engine so asyncpg connections are cleanly closed
        await engine.dispose()


@celery_app.task(name="backend.app.workers.process_document_task")
def process_document_task(document_id: str):
    asyncio.run(_process_document_async(document_id))
