import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
from app.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User
from app.models.config import SystemConfig
from app.models.logs import UsageLog, AuditLog
from app.core.security import create_access_token
from datetime import timedelta

router = APIRouter(prefix="/admin", tags=["Admin"])

class ConfigUpdateRequest(BaseModel):
    key: str
    value: Dict[str, Any]
    description: str | None = None

@router.get("/config")
async def get_configs(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT key, value, description FROM system_configs"
    res = await db.execute(text(sql))
    return [{"key": r[0], "value": r[1], "description": r[2]} for r in res.all()]

@router.put("/config")
async def update_config(
    request: ConfigUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    import json
    # Insert or update
    sql = """
        INSERT INTO system_configs (key, value, description) 
        VALUES (:key, :value, :description)
        ON CONFLICT (key) DO UPDATE SET value = EXCLUDED.value, description = EXCLUDED.description
    """
    await db.execute(text(sql), {"key": request.key, "value": json.dumps(request.value), "description": request.description})
    await db.commit()
    return {"status": "success"}

@router.get("/usage")
async def get_usage_logs(
    user_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, le=500),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    if user_id:
        sql = "SELECT id, user_id, action_type, tokens_used, timestamp FROM usage_logs WHERE user_id = :user_id ORDER BY timestamp DESC LIMIT :limit"
        res = await db.execute(text(sql), {"user_id": str(user_id), "limit": limit})
    else:
        sql = "SELECT id, user_id, action_type, tokens_used, timestamp FROM usage_logs ORDER BY timestamp DESC LIMIT :limit"
        res = await db.execute(text(sql), {"limit": limit})
    return [{"id": str(r[0]), "user_id": str(r[1]), "action_type": r[2], "tokens_used": r[3], "timestamp": r[4]} for r in res.all()]

@router.get("/audit")
async def get_audit_logs(
    user_id: uuid.UUID | None = Query(None),
    limit: int = Query(50, le=500),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # filter by target_id if user_id is provided, else get all
    if user_id:
        sql = "SELECT id, admin_id, action, target_id, details, timestamp FROM audit_logs WHERE target_id = :target_id ORDER BY timestamp DESC LIMIT :limit"
        res = await db.execute(text(sql), {"target_id": str(user_id), "limit": limit})
    else:
        sql = "SELECT id, admin_id, action, target_id, details, timestamp FROM audit_logs ORDER BY timestamp DESC LIMIT :limit"
        res = await db.execute(text(sql), {"limit": limit})
    return [{"id": str(r[0]), "admin_id": str(r[1]) if r[1] else None, "action": r[2], "target_id": r[3], "details": r[4], "timestamp": r[5]} for r in res.all()]

@router.post("/impersonate/{target_user_id}")
async def impersonate_user(
    target_user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, email, is_admin FROM users WHERE id = :id"
    res = await db.execute(text(sql), {"id": str(target_user_id)})
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="User not found")
        
    access_token_expires = timedelta(minutes=60) # 1 hour impersonation
    access_token = create_access_token(
        data={"sub": row[1], "id": str(row[0]), "impersonator": str(admin.id)}, 
        expires_delta=access_token_expires
    )
    
    # Log the impersonation action
    audit_sql = "INSERT INTO audit_logs (admin_id, action, target_id) VALUES (:admin_id, 'impersonate_user', :target_id)"
    await db.execute(text(audit_sql), {"admin_id": str(admin.id), "target_id": str(target_user_id)})
    await db.commit()
    
    return {"access_token": access_token, "token_type": "bearer", "role": "admin" if row[2] else "user"}

class RoleUpdateRequest(BaseModel):
    role: str

class SubjectCreateRequest(BaseModel):
    name: str
    academic_levels: List[str]

class SubjectUpdateRequest(BaseModel):
    name: str | None = None
    academic_levels: List[str] | None = None

class ExamTypeCreateRequest(BaseModel):
    name: str
    guidelines: Dict[str, Any]

@router.get("/users")
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, email, is_admin, created_at FROM users ORDER BY created_at DESC"
    result = await db.execute(text(sql))
    users = [{"id": str(r[0]), "email": r[1], "role": "admin" if r[2] else "user", "created_at": r[3]} for r in result.all()]
    return users

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: uuid.UUID,
    request: RoleUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    is_admin = request.role == "admin"
    sql = "UPDATE users SET is_admin = :is_admin WHERE id = :id RETURNING id"
    result = await db.execute(text(sql), {"is_admin": is_admin, "id": str(user_id)})
    if not result.first():
        raise HTTPException(status_code=404, detail="User not found")
    await db.commit()
    return {"status": "success", "new_role": request.role}

@router.delete("/users/{user_id}")
async def deactivate_user(
    user_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # Depending on implementation, you might soft delete or hard delete. Hard deleting here for simplicity.
    sql = "DELETE FROM users WHERE id = :id"
    await db.execute(text(sql), {"id": str(user_id)})
    await db.commit()
    return {"status": "deleted"}

@router.get("/stats")
async def dashboard_stats(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    stats = {}
    
    res = await db.execute(text("SELECT COUNT(*) FROM users"))
    stats['total_users'] = res.scalar() or 0
    
    res = await db.execute(text("SELECT COUNT(*) FROM documents"))
    stats['total_documents'] = res.scalar() or 0
    
    res = await db.execute(text("SELECT COUNT(*) FROM questions"))
    stats['total_questions'] = res.scalar() or 0
    
    res = await db.execute(text("SELECT COUNT(*) FROM chat_sessions"))
    stats['active_chat_sessions'] = res.scalar() or 0

    return stats

@router.get("/activity")
async def get_recent_activity(
    user_email: str | None = Query(None),
    activity_type: str | None = Query(None),
    limit: int = Query(20, le=100),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    # This combines activities from different tables: Documents, ChatSessions, QuestionPapers
    # It constructs a unified list.
    
    activities = []
    
    # 1. Documents
    if not activity_type or activity_type == "document":
        doc_sql = """
            SELECT d.id, d.filename as title, d.created_at, u.email 
            FROM documents d 
            JOIN users u ON d.user_id = u.id 
            ORDER BY d.created_at DESC LIMIT :limit
        """
        doc_res = await db.execute(text(doc_sql), {"limit": limit})
        for r in doc_res.all():
            activities.append({
                "id": str(r[0]),
                "type": "document",
                "title": r[1],
                "created_at": r[2],
                "user_email": r[3]
            })
            
    # 2. Chat Sessions
    if not activity_type or activity_type == "chat":
        chat_sql = """
            SELECT c.id, c.title, c.created_at, u.email 
            FROM chat_sessions c 
            JOIN users u ON c.user_id = u.id 
            ORDER BY c.created_at DESC LIMIT :limit
        """
        chat_res = await db.execute(text(chat_sql), {"limit": limit})
        for r in chat_res.all():
            activities.append({
                "id": str(r[0]),
                "type": "chat",
                "title": r[1],
                "created_at": r[2],
                "user_email": r[3]
            })
            
    # 3. Question Papers
    if not activity_type or activity_type == "question":
        q_sql = """
            SELECT q.id, q.title as title, q.created_at, u.email 
            FROM question_papers q 
            JOIN users u ON q.user_id = u.id 
            ORDER BY q.created_at DESC LIMIT :limit
        """
        q_res = await db.execute(text(q_sql), {"limit": limit})
        for r in q_res.all():
            activities.append({
                "id": str(r[0]),
                "type": "question",
                "title": r[1], # exam_type is used as title
                "created_at": r[2],
                "user_email": r[3]
            })

    # Filter by user_email if provided
    if user_email:
        activities = [a for a in activities if user_email.lower() in a["user_email"].lower()]

    # Sort by created_at descending and limit
    activities.sort(key=lambda x: x["created_at"], reverse=True)
    return activities[:limit]

@router.post("/subjects")
async def create_subject(
    request: SubjectCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    import json
    from sqlalchemy.exc import IntegrityError
    sid = uuid.uuid4()
    sql = "INSERT INTO subjects (id, name, academic_levels) VALUES (:id, :name, :academic_levels) RETURNING id"
    try:
        await db.execute(text(sql), {"id": str(sid), "name": request.name, "academic_levels": json.dumps(request.academic_levels)})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Subject already exists")
    return {"id": str(sid), "name": request.name}

@router.get("/subjects")
async def admin_list_subjects(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, name, academic_levels FROM subjects ORDER BY name ASC"
    res = await db.execute(text(sql))
    return [{"id": str(r[0]), "name": r[1], "academic_levels": r[2]} for r in res.all()]

@router.put("/subjects/{subject_id}")
async def update_subject(
    subject_id: uuid.UUID,
    request: SubjectUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    import json
    from sqlalchemy.exc import IntegrityError
    
    # Check if subject exists
    check_sql = "SELECT id, name, academic_levels FROM subjects WHERE id = :id"
    res = await db.execute(text(check_sql), {"id": str(subject_id)})
    row = res.first()
    if not row:
        raise HTTPException(status_code=404, detail="Subject not found")
        
    new_name = request.name if request.name is not None else row[1]
    new_levels = json.dumps(request.academic_levels) if request.academic_levels is not None else row[2]
    
    update_sql = "UPDATE subjects SET name = :name, academic_levels = :levels WHERE id = :id RETURNING id"
    try:
        await db.execute(text(update_sql), {"name": new_name, "levels": new_levels, "id": str(subject_id)})
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Subject with this name already exists")
        
    return {"status": "success", "id": str(subject_id)}

@router.delete("/subjects/{subject_id}")
async def delete_subject(
    subject_id: uuid.UUID,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "DELETE FROM subjects WHERE id = :id"
    await db.execute(text(sql), {"id": str(subject_id)})
    await db.commit()
    return {"status": "success"}

@router.post("/exam-types")
async def create_exam_type(
    request: ExamTypeCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    eid = uuid.uuid4()
    import json
    sql = "INSERT INTO exam_types (id, name, guidelines) VALUES (:id, :name, :guidelines) RETURNING id"
    await db.execute(text(sql), {"id": str(eid), "name": request.name, "guidelines": json.dumps(request.guidelines)})
    await db.commit()
    return {"id": str(eid), "name": request.name}

@router.get("/exam-types")
async def admin_list_exam_types(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, name, guidelines FROM exam_types ORDER BY name ASC"
    res = await db.execute(text(sql))
    return [{"id": str(r[0]), "name": r[1], "guidelines": r[2]} for r in res.all()]

class FewShotExamplesUpdateRequest(BaseModel):
    few_shot_examples: Dict[str, Any]

@router.put("/exam-types/{exam_type_id}/few-shot-examples")
async def update_few_shot_examples(
    exam_type_id: uuid.UUID,
    request: FewShotExamplesUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    import json
    sql = "UPDATE exam_types SET few_shot_examples = :examples WHERE id = :id RETURNING id"
    result = await db.execute(text(sql), {"examples": json.dumps(request.few_shot_examples), "id": str(exam_type_id)})
    if not result.first():
        raise HTTPException(status_code=404, detail="Exam type not found")
    await db.commit()
    return {"status": "success"}

@router.post("/exam-types/{exam_type_id}/upload-few-shot")
async def upload_few_shot_examples_file(
    exam_type_id: uuid.UUID,
    file: UploadFile = File(...),
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    import io
    import json
    import PyPDF2
    
    # Check if exam type exists
    sql_check = "SELECT id FROM exam_types WHERE id = :id"
    res = await db.execute(text(sql_check), {"id": str(exam_type_id)})
    if not res.first():
        raise HTTPException(status_code=404, detail="Exam type not found")
        
    try:
        content = await file.read()
        extracted_text = ""
        
        if file.filename.endswith('.pdf'):
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            for page in pdf_reader.pages:
                extracted_text += page.extract_text() + "\n"
        elif file.filename.endswith('.txt'):
            extracted_text = content.decode('utf-8')
        else:
            raise HTTPException(status_code=400, detail="Only PDF or TXT files are supported")
            
        # Use LLM to extract example questions from the text
        from app.services.chatbot_service import chatbot_service
        import google.generativeai as genai
        from app.core.llm_wrapper import LLMWrapper
        
        prompt = f"""
You are an expert educational data extractor.
I am providing you with the text of a previous year question paper.
Extract 3-5 of the best, most representative questions from this text to serve as "few-shot examples" for an LLM that will generate similar questions later.
Include a mix of difficulties if possible.

TEXT:
{extracted_text[:15000]}

Format your output as a JSON dict with an "examples" key containing a list of strings.
Example:
{{
  "examples": [
    "Q1: What is the significance of the Battle of Hastings? (5 marks)",
    "Q2: Calculate the derivative of f(x) = x^2 + 2x. (3 marks)"
  ]
}}
Return ONLY valid JSON.
"""
        response = await LLMWrapper.generate_content_async(
            model_name='gemini-2.5-flash',
            prompt=prompt,
            stream=False,
            generation_config=genai.GenerationConfig(response_mime_type="application/json")
        )
        
        try:
            few_shot_data = json.loads(response.text)
        except json.JSONDecodeError:
            raise ValueError("Failed to parse LLM response into JSON")
            
        # Save to database
        sql_update = "UPDATE exam_types SET few_shot_examples = :examples WHERE id = :id"
        await db.execute(text(sql_update), {"examples": json.dumps(few_shot_data), "id": str(exam_type_id)})
        await db.commit()
        
        return {"status": "success", "extracted_examples": few_shot_data.get("examples", [])}
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")

