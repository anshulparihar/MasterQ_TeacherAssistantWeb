import uuid
from typing import List, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Body, File, UploadFile
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import asyncio
from app.database import get_db
from app.core.deps import get_current_user, get_current_admin
from app.models.user import User

router = APIRouter(prefix="/admin", tags=["Admin"])

class RoleUpdateRequest(BaseModel):
    role: str

class SubjectCreateRequest(BaseModel):
    name: str
    academic_levels: List[str]

class ExamTypeCreateRequest(BaseModel):
    name: str
    guidelines: Dict[str, Any]

@router.get("/users")
async def list_users(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, email, role, created_at FROM users ORDER BY created_at DESC"
    result = await db.execute(text(sql))
    users = [{"id": str(r[0]), "email": r[1], "role": r[2], "created_at": r[3]} for r in result.all()]
    return users

@router.put("/users/{user_id}/role")
async def change_user_role(
    user_id: uuid.UUID,
    request: RoleUpdateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "UPDATE users SET role = :role WHERE id = :id RETURNING id"
    result = await db.execute(text(sql), {"role": request.role, "id": str(user_id)})
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

@router.post("/subjects")
async def create_subject(
    request: SubjectCreateRequest,
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sid = uuid.uuid4()
    sql = "INSERT INTO subjects (id, name) VALUES (:id, :name) RETURNING id"
    await db.execute(text(sql), {"id": str(sid), "name": request.name})
    await db.commit()
    return {"id": str(sid), "name": request.name}

@router.get("/subjects")
async def admin_list_subjects(
    admin: User = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db)
):
    sql = "SELECT id, name FROM subjects ORDER BY name ASC"
    res = await db.execute(text(sql))
    return [{"id": str(r[0]), "name": r[1]} for r in res.all()]

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
        model = genai.GenerativeModel('gemini-2.5-flash', generation_config={"response_mime_type": "application/json"})
        response = await asyncio.to_thread(model.generate_content, prompt)
        
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

