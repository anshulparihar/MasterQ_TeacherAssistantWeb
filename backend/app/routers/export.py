from fastapi import APIRouter, Depends, Query
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.export_service import export_service

router = APIRouter()

@router.get("/questions/papers/{paper_id}/export")
async def export_paper(
    paper_id: UUID,
    format: str = Query(..., pattern="^(pdf|docx)$"),
    include_answers: bool = Query(False),
    include_explanations: bool = Query(False),
    include_hints: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Export question paper as PDF or DOCX.
    Returns file download response.
    """
    file_bytes, filename, mime_type = await export_service.export_paper(
        db, paper_id, current_user.id,
        format, include_answers, include_explanations, include_hints
    )
    
    return Response(
        content=file_bytes,
        media_type=mime_type,
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Content-Length": str(len(file_bytes))
        }
    )
