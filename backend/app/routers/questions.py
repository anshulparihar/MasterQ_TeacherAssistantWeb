import uuid
from typing import List, Dict
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.question_generator import question_generator
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/questions", tags=["Questions"])

from app.schemas.question import QuestionGenerationRequest

class SwapRequest(BaseModel):
    original_question_id: str
    recommendation_question_id: str

@router.post("/generate")
async def generate_questions(
    request: QuestionGenerationRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        logger.info("question_generation_requested", user_id=str(user.id), subject_id=str(request.subject_id), exam_type_id=str(request.exam_type_id))
        logger.info(f'request.model_dump():{request.model_dump()}')
        response = await question_generator.generate_paper(db, user.id, request.model_dump())
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        raise HTTPException(status_code=500, detail="Generation failed")

from sqlalchemy.orm import joinedload
from sqlalchemy import select
from app.models.question import QuestionPaper

@router.get("/papers/me")
async def get_my_papers(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    query = (
        select(QuestionPaper)
        .options(joinedload(QuestionPaper.subject), joinedload(QuestionPaper.questions))
        .where(QuestionPaper.user_id == user.id)
        .order_by(QuestionPaper.created_at.desc())
    )
    result = await db.execute(query)
    papers = result.unique().scalars().all()
    
    return [
        {
            "id": str(p.id),
            "title": p.title,
            "created_at": p.created_at,
            "subject": {"name": p.subject.name} if p.subject else None,
            "questions": [{"id": str(q.id)} for q in p.questions]
        }
        for p in papers
    ]

@router.get("/papers/{paper_id}")
async def get_paper(
    paper_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership
    sql_check = "SELECT id, title FROM question_papers WHERE id = :id AND user_id = :user_id"
    res = await db.execute(text(sql_check), {"id": str(paper_id), "user_id": str(user.id)})
    paper = res.first()
    if not paper:
        raise HTTPException(status_code=404, detail="Paper not found")
        
    sql_q = "SELECT id,text,type,options,correct_answer, model_answer,difficulty,topic_id,diagram_url, diagram_type,explanation, hint,marks,is_recommendation FROM questions WHERE question_paper_id = :id AND is_recommendation = false"
    res_q = await db.execute(text(sql_q), {"id": str(paper_id)})
    
    questions = []
    for row in res_q.all():
        q_dict = dict(row._mapping)
        questions.append(q_dict)
        
    return {
        "paper_id": paper[0],
        "title": paper[1],
        "questions": questions
    }

@router.get("/papers/{paper_id}/recommendations")
async def get_paper_recommendations(
    paper_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sql_check = "SELECT id FROM question_papers WHERE id = :id AND user_id = :user_id"
    res = await db.execute(text(sql_check), {"id": str(paper_id), "user_id": str(user.id)})
    if not res.first():
        raise HTTPException(status_code=404, detail="Paper not found")
        
    sql_q = "SELECT * FROM questions WHERE question_paper_id = :id AND is_recommendation = true"
    res_q = await db.execute(text(sql_q), {"id": str(paper_id)})
    return [dict(row._mapping) for row in res_q.all()]

@router.post("/swap")
async def swap_question(
    request: SwapRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sql_orig = """
    SELECT q.id, q.question_paper_id, qp.user_id 
    FROM questions q
    JOIN question_papers qp ON q.question_paper_id = qp.id
    WHERE q.id = :id
    """
    res_orig = await db.execute(text(sql_orig), {"id": request.original_question_id})
    orig_row = res_orig.first()
    if not orig_row or str(orig_row[2]) != str(user.id):
        raise HTTPException(status_code=403, detail="Original question not found or unauthorized")
        
    sql_rec = """
    SELECT id, question_paper_id, is_recommendation 
    FROM questions 
    WHERE id = :id
    """
    res_rec = await db.execute(text(sql_rec), {"id": request.recommendation_question_id})
    rec_row = res_rec.first()
    
    if not rec_row or str(rec_row[1]) != str(orig_row[1]) or not rec_row[2]:
        raise HTTPException(status_code=400, detail="Invalid recommendation question")
        
    await db.execute(text("UPDATE questions SET is_recommendation = true WHERE id = :id"), {"id": request.original_question_id})
    await db.execute(text("UPDATE questions SET is_recommendation = false WHERE id = :id"), {"id": request.recommendation_question_id})
    await db.commit()
    
    sql_fetch = "SELECT * FROM questions WHERE id = :id"
    res_fetch = await db.execute(text(sql_fetch), {"id": request.recommendation_question_id})
    return {"status": "success", "new_question": dict(res_fetch.first()._mapping)}

@router.delete("/papers/{paper_id}")
async def delete_paper(
    paper_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sql = "DELETE FROM question_papers WHERE id = :id AND user_id = :user_id"
    await db.execute(text(sql), {"id": str(paper_id), "user_id": str(user.id)})
    await db.commit()
    return {"status": "deleted"}
