import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.database import get_db
from app.core.deps import get_current_user
from app.models.user import User
from app.services.chatbot_service import chatbot_service

router = APIRouter(prefix="/chatbot", tags=["Chatbot"])

class CreateSessionRequest(BaseModel):
    selected_document_ids: List[uuid.UUID] = []
    selected_paper_ids: List[uuid.UUID] = []

class ChatMessageRequest(BaseModel):
    message: str
    selected_document_ids: List[uuid.UUID] = []
    selected_paper_ids: List[uuid.UUID] = []

@router.post("/sessions")
async def create_session(
    request: CreateSessionRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        session = await chatbot_service.create_session(
            db=db,
            user_id=user.id,
            selected_document_ids=request.selected_document_ids,
            selected_paper_ids=request.selected_paper_ids
        )
        return session
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to create session")

@router.get("/sessions/me")
async def get_my_sessions(
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, title, created_at FROM chat_sessions WHERE user_id = :user_id ORDER BY created_at DESC"
    result = await db.execute(text(sql), {"user_id": str(user.id)})
    return [{"id": row[0], "title": row[1], "created_at": row[2]} for row in result.all()]

@router.get("/sessions/{session_id}")
async def get_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        messages = await chatbot_service.get_session_history(db, session_id, user.id)
        return {"session_id": str(session_id), "messages": messages}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to fetch session")

@router.post("/sessions/{session_id}/message")
async def send_message(
    session_id: uuid.UUID,
    request: ChatMessageRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        response = await chatbot_service.chat(
            db=db,
            user_id=user.id,
            session_id=session_id,
            message=request.message,
            selected_document_ids=request.selected_document_ids,
            selected_paper_ids=request.selected_paper_ids
        )
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process message")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: uuid.UUID,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    # Verify ownership before delete
    sql_check = "SELECT id FROM chat_sessions WHERE id = :id AND user_id = :user_id"
    res = await db.execute(text(sql_check), {"id": str(session_id), "user_id": str(user.id)})
    if not res.first():
        raise HTTPException(status_code=404, detail="Session not found")
        
    sql_del_msgs = "DELETE FROM chat_messages WHERE session_id = :id"
    await db.execute(text(sql_del_msgs), {"id": str(session_id)})
    
    sql_del = "DELETE FROM chat_sessions WHERE id = :id"
    await db.execute(text(sql_del), {"id": str(session_id)})
    await db.commit()
    
    return {"status": "deleted"}
