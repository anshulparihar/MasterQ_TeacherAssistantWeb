from typing import List, Any
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.database import get_db

router = APIRouter(prefix="/exam-types", tags=["Exam Types"])

@router.get("")
async def list_exam_types(db: AsyncSession = Depends(get_db)):
    sql = "SELECT id, name, guidelines FROM exam_types ORDER BY name ASC"
    res = await db.execute(text(sql))
    return [{"id": str(r[0]), "name": r[1], "guidelines": r[2]} for r in res.all()]

@router.get("/{exam_type_id}")
async def get_exam_type(exam_type_id: str, db: AsyncSession = Depends(get_db)):
    sql = "SELECT id, name, guidelines FROM exam_types WHERE id = :id"
    res = await db.execute(text(sql), {"id": exam_type_id})
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Exam Type not found")
    return {"id": str(row[0]), "name": row[1], "guidelines": row[2]}
