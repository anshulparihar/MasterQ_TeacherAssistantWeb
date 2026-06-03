import uuid
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.services.topic_service import topic_service

router = APIRouter(prefix="/topics", tags=["Topics"])

@router.get("/by-subject")
async def get_topics_by_subject(
    subject_id: uuid.UUID = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Returns aggregated topics + subtopics from:
    - All ADMIN documents with matching subject_id
    - Current user's OWN documents with matching subject_id
    
    Aggregation: group by topic_name, merge subtopic lists (deduplicated),
    average importance_score.
    """
    sql = """
    SELECT 
        dt.topic_name,
        array_agg(DISTINCT st.subtopic) AS subtopics,
        AVG(dt.importance_score) AS importance_score
    FROM document_topics dt
    CROSS JOIN LATERAL jsonb_array_elements_text(dt.subtopics::jsonb) AS st(subtopic)
    JOIN documents d ON dt.document_id = d.id
    WHERE d.subject_id = :subject_id
      AND d.status = 'ready'
      AND (d.doc_type = 'admin' OR d.user_id = :user_id)
    GROUP BY dt.topic_name
    ORDER BY AVG(dt.importance_score) DESC
    """
    
    result = await db.execute(text(sql), {
        "subject_id": str(subject_id),
        "user_id": str(current_user.id)
    })
    
    response_data = []
    for row in result.all():
        response_data.append({
            "topic_name": row[0],
            "subtopics": row[1] if row[1] else [],
            "importance_score": float(row[2]) if row[2] else 0.0
        })
        
    return response_data

@router.get("/document/{document_id}")
async def get_document_topics(
    document_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify access to document
    sql = "SELECT doc_type, user_id FROM documents WHERE id = :doc_id"
    result = await db.execute(text(sql), {"doc_id": str(document_id)})
    doc = result.first()
    
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found")
        
    doc_type, doc_user_id = doc[0], doc[1]
    
    if doc_type != 'admin' and doc_user_id != user.id:
        raise HTTPException(status_code=403, detail="Access denied")
        
    topics = await topic_service.get_topics_for_documents(db, [document_id])
    return topics

@router.get("/user/me")
async def get_user_topics(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Get all user document IDs
    sql = "SELECT id FROM documents WHERE user_id = :user_id"
    result = await db.execute(text(sql), {"user_id": str(user.id)})
    doc_ids = [row[0] for row in result.all()]
    
    if not doc_ids:
        return []
        
    topics = await topic_service.get_topics_for_documents(db, doc_ids)
    return topics

@router.get("/admin")
async def get_admin_topics(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Get all admin document IDs
    sql = "SELECT id FROM documents WHERE doc_type = 'admin'"
    result = await db.execute(text(sql))
    doc_ids = [row[0] for row in result.all()]
    
    if not doc_ids:
        return []
        
    topics = await topic_service.get_topics_for_documents(db, doc_ids)
    return topics
