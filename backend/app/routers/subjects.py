from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/subjects", tags=["Subjects"])

@router.get("")
async def list_subjects(db: AsyncSession = Depends(get_db)):
    sql = "SELECT id, name FROM subjects ORDER BY name ASC"
    res = await db.execute(text(sql))
    return [{"id": str(r[0]), "name": r[1]} for r in res.all()]

@router.get("/{subject_id}")
async def get_subject(subject_id: str, db: AsyncSession = Depends(get_db)):
    sql = "SELECT id, name FROM subjects WHERE id = :id"
    res = await db.execute(text(sql), {"id": subject_id})
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Subject not found")
    return {"id": str(row[0]), "name": row[1]}

@router.get("/{subject_id}/academic-levels")
async def get_subject_academic_levels(subject_id: str, db: AsyncSession = Depends(get_db)):
    sql = """
    SELECT DISTINCT academic_level
    FROM documents
    WHERE subject_id = :id AND academic_level IS NOT NULL
    """
    res = await db.execute(text(sql), {"id": subject_id})
    return [r[0] for r in res.all() if r[0]]
