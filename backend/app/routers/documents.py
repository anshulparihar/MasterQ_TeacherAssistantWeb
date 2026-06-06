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
    """
    Internal helper function to handle document uploads, MinIO storage, and database registration.

    - **file**: The uploaded file object.
    - **db**: Asynchronous database session.
    - **user_id**: ID of the uploading user (None for admin files).
    - **doc_type**: String specifying document type ('admin' or 'user').
    - **bucket**: MinIO bucket name where the file will be stored.
    - **subject_id**: Optional Subject UUID target for the document.
    - **academic_level**: Optional academic level target for the document.
    """
    # Read the upload file bytes into memory to validate size.
    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large. Max 50MB allowed.")
        
    # Extract extension and validate that it is supported (PDF, DOCX, TXT, MD).
    ext = file.filename.split('.')[-1].lower()
    if ext not in ['pdf', 'docx', 'txt', 'md']:
        raise HTTPException(status_code=400, detail="Unsupported file type.")
        
    # Generate unique key to prevent name collisions in Object Storage.
    doc_uuid = uuid.uuid4()
    s3_key = f"{doc_uuid}_{file.filename}"
    
    # Upload the document bytes directly to MinIO Object Storage bucket.
    storage_service.upload_file(bucket, s3_key, file_bytes, file.content_type)
    
    # Create the SQL record for this document tracking status.
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
    # Commit the transaction asynchronously to save changes to DB.
    await db.commit()
    
    # Trigger the asynchronous Celery worker task to process the document (parse, chunk, embed, and extract topics).
    logger.info("document_upload_requested", document_id=str(doc_uuid), user_id=str(user_id), doc_type=doc_type)
    process_document_task.delay(str(doc_uuid))
    
    # Return response indicating that document is registered and processing has begun.
    return {"document_id": str(doc_uuid), "status": "processing"}

@router.post("/admin/upload")
async def upload_admin_document(
    file: UploadFile = File(...),
    subject_id: uuid.UUID | None = Form(None),
    academic_level: str | None = Form(None),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Endpoint for admins to upload global documents to the admin bucket.

    - **file**: The file to upload (Max 50MB, PDF/DOCX/TXT/MD).
    - **subject_id**: Subject classification identifier.
    - **academic_level**: Level classification identifier.
    """
    # Delegate to the internal helper using the admin-specific bucket name.
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
    """
    Endpoint for teachers to upload private files to their user bucket.

    - **file**: The file to upload (Max 50MB, PDF/DOCX/TXT/MD).
    - **subject_id**: Subject classification identifier.
    - **academic_level**: Level classification identifier.
    """
    # Delegate to the internal helper using the user-specific bucket and teacher ID.
    return await _upload_document(
        file, db, user_id=user.id, doc_type='user', bucket=settings.MINIO_BUCKET_USER, subject_id=subject_id, academic_level=academic_level
    )

@router.get("/admin")
async def list_admin_documents(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all globally uploaded documents (admin role required).

    - **admin**: Dependency checking that current user is an admin.
    - **db**: Asynchronous database session.
    """
    # Execute database query to retrieve admin documents.
    return await get_admin_documents(db)

from sqlalchemy.orm import joinedload

@router.get("/user/me")
async def get_user_documents(
    subject_id: uuid.UUID | None = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve all processing-ready documents belonging to the authenticated teacher.

    - **subject_id**: Filter documents by a specific subject.
    - **current_user**: Authed teacher.
    - **db**: Asynchronous database session.
    """
    # Build query selecting documents owned by user with status 'ready', eager loading subject relations.
    query = select(Document).options(joinedload(Document.subject)).where(
        Document.user_id == current_user.id,
        Document.status == 'ready'
    )
    # Check if a subject filter is requested and append the filter criteria to the query.
    if subject_id:
        query = query.where(Document.subject_id == subject_id)
    # Execute query asynchronously ordering results by creation timestamp.
    result = await db.execute(query.order_by(Document.created_at.desc()))
    # Retrieve unique scalar document records from result.
    docs = result.unique().scalars().all()
    
    # Format and return list containing document metadata to the frontend.
    return [
        {
            "id": str(d.id),
            "filename": d.filename,
            "doc_type": d.doc_type,
            "status": d.status,
            "subject_id": str(d.subject_id) if d.subject_id else None,
            "subject": {"name": d.subject.name} if getattr(d, 'subject', None) else None,
            "academic_level": d.academic_level,
            "created_at": d.created_at
        }
        for d in docs
    ]

@router.get("/{document_id}/status")
async def get_document_status(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve processing status ('processing', 'ready', 'failed') of a document.

    - **document_id**: UUID of the document to inspect.
    """
    # Query database for the document, validating that current user has access.
    doc = await get_document_by_id(db, document_id, user.id)
    # Return document UUID along with status.
    return {"document_id": str(doc.id), "status": doc.status}

@router.get("/{document_id}")
async def get_document_metadata(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get detailed metadata for a single document owned by the current user.

    - **document_id**: UUID of the document to view.
    """
    # Retrieve the document from the database verifying ownership permissions.
    doc = await get_document_by_id(db, document_id, user.id)
    # Return formatted metadata dictionary.
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
    # Fetch the document by ID and verify that it belongs to the authenticated user.
    doc = await get_document_by_id(db, document_id, user.id)

    # Prevent non-admin users from updating metadata of global/admin documents.
    if doc.doc_type == 'admin':
        raise HTTPException(
            status_code=403,
            detail="Cannot update admin documents via this endpoint. Use the admin endpoint."
        )

    # Initialize a flag to verify if any fields were modified during the request.
    updated = False
    # If a new subject ID is provided, update the document model's subject.
    if subject_id is not None:
        doc.subject_id = subject_id
        updated = True
    # If a new academic level is provided, update the document model's academic level.
    if academic_level is not None:
        doc.academic_level = academic_level
        updated = True

    # If no fields were provided for updating, raise a 400 bad request error.
    if not updated:
        raise HTTPException(status_code=400, detail="No fields provided to update. Pass subject_id and/or academic_level.")

    # Commit modifications to save updated subject/academic level fields in PostgreSQL.
    await db.commit()
    # Refresh SQLAlchemy session object to ensure it reflects current database state.
    await db.refresh(doc)

    # Log metadata updates to structlog for auditing.
    logger.info(
        "document_metadata_updated",
        document_id=str(document_id),
        user_id=str(user.id),
        subject_id=str(doc.subject_id) if doc.subject_id else None,
        academic_level=doc.academic_level
    )
    # Return formatted update summary.
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
    """
    Admin endpoint to update subject_id and/or academic_level on any document.

    - **document_id**: UUID of the document to modify.
    - **admin**: Injected admin verification dependency.
    """
    # Fetch the document bypass user check (user_id=None) allowing access to all documents.
    doc = await get_document_by_id(db, document_id, None)

    # Initialize a flag to check if any modifications were applied.
    updated = False
    # Update subject if provided.
    if subject_id is not None:
        doc.subject_id = subject_id
        updated = True
    # Update academic level if provided.
    if academic_level is not None:
        doc.academic_level = academic_level
        updated = True

    # Raise exception if no field updates were sent in the PATCH payload.
    if not updated:
        raise HTTPException(status_code=400, detail="No fields provided to update.")

    # Apply database transaction commit.
    await db.commit()
    # Pull current object state from PostgreSQL.
    await db.refresh(doc)

    # Log successful admin modifications.
    logger.info(
        "admin_document_metadata_updated",
        document_id=str(document_id),
        admin_id=str(admin.id),
        subject_id=str(doc.subject_id) if doc.subject_id else None,
        academic_level=doc.academic_level
    )
    # Return metadata update confirmation.
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
    """
    Delete a document owned by the authenticated teacher.

    - **document_id**: Target document UUID.
    """
    # Fetch user's own document record ensuring authorization permissions check.
    doc = await get_document_by_id(db, document_id, user.id)
    # Prevent normal users from deleting global/admin files.
    if doc.doc_type == 'admin':
        raise HTTPException(status_code=403, detail="Cannot delete admin documents. Use the admin delete endpoint.")
    
    # Select user bucket name based on document classification.
    bucket = settings.MINIO_BUCKET_ADMIN if doc.doc_type == 'admin' else settings.MINIO_BUCKET_USER
    # Connect with MinIO and remove target file bytes from Object Storage.
    storage_service.delete_file(bucket, doc.s3_key)
    
    # Asynchronously delete document record from DB (foreign key cascades will drop related chunks).
    await db.delete(doc)
    # Finalize the database session transaction changes.
    await db.commit()
    
    # Send success response confirmation.
    return {"message": "Document deleted"}

@router.delete("/admin/{document_id}")
async def admin_delete_document(
    document_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Admin-only endpoint to delete any document from both storage and database.

    - **document_id**: UUID of the document to drop.
    """
    # Fetch document bypassing owner security check.
    doc = await get_document_by_id(db, document_id, None)
    
    # Select bucket mapping dynamically.
    bucket = settings.MINIO_BUCKET_ADMIN if doc.doc_type == 'admin' else settings.MINIO_BUCKET_USER
    # Remove file from Object Storage.
    storage_service.delete_file(bucket, doc.s3_key)
    
    # Delete from local PostgreSQL database.
    await db.delete(doc)
    # Finalize deletion transaction.
    await db.commit()
    
    # Return deletion status string.
    return {"message": "Admin document deleted"}
