import uuid
import aiofiles
import os
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Query, Form
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.document import Document
from app.services.storage_service import storage_service
from app.services.document_service import get_admin_documents, get_document_by_id
from app.workers.document_worker import process_document_task
from app.config import settings
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/documents", tags=["Documents"])

MAX_FILE_SIZE = 50 * 1024 * 1024 # 50 MB

async def _upload_document(
    file: UploadFile, 
    db: AsyncSession, 
    user_id: uuid.UUID | None, 
    doc_type: str, 
    bucket: str,
    subject_id: uuid.UUID | None = None,
    academic_level: str | None = None
):
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB allowed.")
        
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['pdf', 'docx', 'txt', 'md']:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
        
    # Generate unique key
    doc_uuid = uuid.uuid4()
    s3_key = f"{doc_uuid}_{file.filename}"
    
    # Upload to MinIO
    storage_service.upload_file(bucket, s3_key, file_bytes, file.content_type)
    
    # Create DB record
    db_doc = Document(
        id=doc_uuid,
        filename=file.filename,
        doc_type=doc_type,
        user_id=user_id,
        s3_key=s3_key,
        status="processing",
        chunk_count=0,
        subject_id=subject_id,
        academic_level=academic_level
    )
    db.add(db_doc)
    await db.commit()
    
    # Trigger Celery task
    logger.info("document_upload_requested", document_id=str(doc_uuid), user_id=str(user_id), doc_type=doc_type)
    process_document_task.delay(str(doc_uuid))
    
    return {"document_id": str(doc_uuid), "status": "processing"}

@router.post("/admin/upload")
async def upload_admin_document(
    file: UploadFile = File(...),
    subject_id: uuid.UUID | None = Form(None),
    academic_level: str | None = Form(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    return await _upload_document(
        file, db, user_id=None, doc_type='admin', bucket=settings.MINIO_BUCKET_ADMIN, subject_id=subject_id, academic_level=academic_level
    )

@router.post("/user/upload")
async def upload_user_document(
    file: UploadFile = File(...),
    subject_id: uuid.UUID | None = Form(None),
    academic_level: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    return await _upload_document(
        file, db, user_id=user.id, doc_type='user', bucket=settings.MINIO_BUCKET_USER, subject_id=subject_id, academic_level=academic_level
    )

@router.get("/admin")
async def list_admin_documents(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    return await get_admin_documents(db)

@router.get("/user/me")
async def get_user_documents(
    subject_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = select(Document).where(
        Document.user_id == current_user.id,
        Document.status == 'ready'
    )
    if subject_id:
        query = query.where(Document.subject_id == subject_id)
    result = await db.execute(query.order_by(Document.created_at.desc())) # upload_date isn't in model, created_at is
    return result.scalars().all()

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, document_id, user.id)
    return {"document_id": str(doc.id), "status": doc.status}

@router.get("/{document_id}")
async def get_document_metadata(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get metadata for a single document owned by the current user."""
    doc = await get_document_by_id(db, document_id, user.id)
    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "doc_type": doc.doc_type,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "subject_id": str(doc.subject_id) if doc.subject_id else None,
        "academic_level": doc.academic_level,
        "created_at": doc.created_at,
    }

@router.patch("/{document_id}/metadata")
async def update_document_metadata(
    document_id: uuid.UUID,
    subject_id: uuid.UUID | None = Form(None),
    academic_level: str | None = Form(None),
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update subject_id and/or academic_level on an existing document.
    Use this to tag documents that were uploaded before these fields existed.
    Only the document owner can update their own document.
    """
    doc = await get_document_by_id(db, document_id, user.id)

    if doc.doc_type == 'admin':
        raise HTTPException(
            status_code=403,
            detail="Cannot update admin documents via this endpoint. Use the admin endpoint."
        )

    updated = False
    if subject_id is not None:
        doc.subject_id = subject_id
        updated = True
    if academic_level is not None:
        doc.academic_level = academic_level
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="No fields provided to update. Pass subject_id and/or academic_level.")

    await db.commit()
    await db.refresh(doc)

    logger.info(
        "document_metadata_updated",
        document_id=str(document_id),
        user_id=str(user.id),
        subject_id=str(doc.subject_id) if doc.subject_id else None,
        academic_level=doc.academic_level
    )
    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "subject_id": str(doc.subject_id) if doc.subject_id else None,
        "academic_level": doc.academic_level,
        "status": doc.status,
        "message": "Metadata updated successfully"
    }

@router.patch("/admin/{document_id}/metadata")
async def admin_update_document_metadata(
    document_id: uuid.UUID,
    subject_id: uuid.UUID | None = Form(None),
    academic_level: str | None = Form(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """Admin endpoint to update subject_id and/or academic_level on any document."""
    doc = await get_document_by_id(db, document_id, None)

    updated = False
    if subject_id is not None:
        doc.subject_id = subject_id
        updated = True
    if academic_level is not None:
        doc.academic_level = academic_level
        updated = True

    if not updated:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    await db.commit()
    await db.refresh(doc)

    logger.info(
        "admin_document_metadata_updated",
        document_id=str(document_id),
        admin_id=str(admin.id),
        subject_id=str(doc.subject_id) if doc.subject_id else None,
        academic_level=doc.academic_level
    )
    return {
        "document_id": str(doc.id),
        "filename": doc.filename,
        "subject_id": str(doc.subject_id) if doc.subject_id else None,
        "academic_level": doc.academic_level,
        "status": doc.status,
        "message": "Admin metadata updated successfully"
    }

@router.delete("/{document_id}")
async def delete_document(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, document_id, user.id)
    if doc.doc_type == 'admin':
        raise HTTPException(status_code=403, detail="Cannot delete admin documents. Use the admin delete endpoint.")
    
    # Delete from MinIO
    bucket = settings.MINIO_BUCKET_ADMIN if doc.doc_type == 'admin' else settings.MINIO_BUCKET_USER
    storage_service.delete_file(bucket, doc.s3_key)
    
    # Delete from DB (cascade handles chunks)
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Document deleted"}

@router.delete("/admin/{document_id}")
async def admin_delete_document(
    document_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    doc = await get_document_by_id(db, document_id, None)
    
    bucket = settings.MINIO_BUCKET_ADMIN if doc.doc_type == 'admin' else settings.MINIO_BUCKET_USER
    storage_service.delete_file(bucket, doc.s3_key)
    
    await db.delete(doc)
    await db.commit()
    
    return {"message": "Admin document deleted"}
