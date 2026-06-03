import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from fastapi import HTTPException, status
from app.models.document import Document

async def get_admin_documents(db: AsyncSession) -> list[Document]:
    result = await db.execute(select(Document).where(Document.doc_type == 'admin'))
    return list(result.scalars().all())

async def get_user_documents(db: AsyncSession, user_id: uuid.UUID) -> list[Document]:
    result = await db.execute(select(Document).where(Document.user_id == user_id))
    return list(result.scalars().all())

async def get_document_by_id(db: AsyncSession, doc_id: uuid.UUID, user_id: uuid.UUID | None = None) -> Document:
    result = await db.execute(select(Document).where(Document.id == doc_id))
    document = result.scalars().first()
    
    if not document:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Document not found")
        
    if user_id is None:
        # Request context is anonymous or requesting admin explicitly
        if document.doc_type != 'admin':
             raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    else:
        # Request context is authenticated user
        # User can access their own docs and admin docs
        if document.doc_type != 'admin' and document.user_id != user_id:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
            
    return document
