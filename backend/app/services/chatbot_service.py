import asyncio
import uuid
import structlog
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
# removed global genai import

from app.config import settings
from app.services.retrieval_service import retrieval_service

logger = structlog.get_logger()
from app.core.llm_wrapper import LLMWrapper

class ChatbotService:
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)

        # self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME) # Using LLMWrapper instead
        self.retrieval_service = retrieval_service
    
    async def chat_stream(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        session_id: uuid.UUID,
        message: str,
        selected_document_ids: list[uuid.UUID],
        selected_paper_ids: list[uuid.UUID]
    ):
        import json
        
        # 1. Retrieve context chunks
        context_chunks, all_references = await self.retrieval_service.retrieve_for_chatbot(
            db=db,
            user_id=user_id,
            query=message,
            selected_document_ids=selected_document_ids,
            selected_paper_ids=selected_paper_ids,
            top_k=15
        )
        
        # 2. Fetch conversation history from DB (last 10 messages for context)
        sql_hist = """
        SELECT role, content FROM chat_messages 
        WHERE session_id = CAST(:session_id AS UUID) 
        ORDER BY created_at DESC LIMIT 10
        """
        hist_res = await db.execute(text(sql_hist), {"session_id": str(session_id)})
        history_rows = hist_res.all()
        # Reverse to chronological order
        history_rows = list(reversed(history_rows))
        
        history_text = ""
        for r in history_rows:
            role = r[0]
            content = r[1]
            history_text += f"{role.upper()}: {content}\n"
            
        # 3. Build prompt
        context_docs = ""
        for c in context_chunks:
            doc_type = c.get('doc_type', 'user')
            doc_filename = c.get('doc_filename', 'Unknown Document')
            
            if doc_type == 'user':
                source_label = doc_filename
            else:
                source_label = "Reference Material"
                
            context_docs += f"[Source: {source_label}]\n{c.get('chunk_text', '')}\n---\n"
            
        # Deduplicate references
        unique_refs = []
        seen = set()
        for ref in all_references:
            doc_id = ref.get('doc_id')
            if doc_id and doc_id not in seen:
                if ref.get('doc_type') == 'admin':
                    continue
                
                unique_refs.append({
                    "document_id": doc_id,
                    "filename": ref.get('doc_filename', 'Unknown'),
                    "doc_type": ref.get('doc_type', 'user')
                })
                seen.add(doc_id)

        system_prompt = f"""
You are a study assistant. You must ONLY answer based on the provided context documents.
If the answer is not present in the context, respond with EXACTLY:
"I don't have information about this in the available documents."
Never use outside knowledge. Never hallucinate.

CONTEXT DOCUMENTS:
{context_docs}

CONVERSATION HISTORY:
{history_text}

USER QUESTION: {message}

Respond helpfully and concisely based ONLY on the context above.
"""

        # 4. Call Gemini with stream
        assistant_reply = ""
        async with self.semaphore:
            response = await LLMWrapper.generate_content_async(
                model_name=settings.GEMINI_MODEL_NAME, 
                prompt=system_prompt, 
                stream=True
            )
            async for chunk in response:
                if chunk.text:
                    assistant_reply += chunk.text
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk.text})}\n\n"
                    
        assistant_reply = assistant_reply.strip()
        
        # 5. Detect "not in context" responses
        exact_fallback = "I don't have information about this in the available documents."
        if exact_fallback.lower() in assistant_reply.lower():
            # Drop references if no information
            unique_refs = []
            
        yield f"data: {json.dumps({'type': 'end', 'references': unique_refs})}\n\n"
            
        # 7. Save user message + assistant response to DB
        user_msg_id = uuid.uuid4()
        asst_msg_id = uuid.uuid4()
        
        sql_insert_user = """
        INSERT INTO chat_messages (id, session_id, role, content, created_at)
        VALUES (CAST(:id AS UUID), CAST(:session_id AS UUID), :role, :content, NOW())
        """
        sql_insert_asst = """
        INSERT INTO chat_messages (id, session_id, role, content, "references", created_at)
        VALUES (CAST(:id AS UUID), CAST(:session_id AS UUID), :role, :content, :references, NOW())
        """
        
        ref_filenames = [r['filename'] for r in unique_refs] if unique_refs else None

        await db.execute(text(sql_insert_user), {"id": str(user_msg_id), "session_id": str(session_id), "role": "user", "content": message})
        await db.execute(text(sql_insert_asst), {"id": str(asst_msg_id), "session_id": str(session_id), "role": "assistant", "content": assistant_reply, "references": ref_filenames})
        await db.commit()
        
    async def create_session(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        selected_document_ids: list[uuid.UUID],
        selected_paper_ids: list[uuid.UUID]
    ) -> dict:
        session_id = uuid.uuid4()
        title = "New Chat Session"
        
        sql = """
        INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at) 
        VALUES (CAST(:id AS UUID), CAST(:user_id AS UUID), :title, NOW(), NOW())
        RETURNING created_at
        """
        res = await db.execute(text(sql), {"id": str(session_id), "user_id": str(user_id), "title": title})
        row = res.first()
        created_at = row[0] if row else None
        await db.commit()
        
        return {
            "id": str(session_id),
            "title": title,
            "created_at": created_at.isoformat() if created_at else None
        }
        
    async def get_session_history(
        self,
        db: AsyncSession,
        session_id: uuid.UUID,
        user_id: uuid.UUID
    ) -> list[dict]:
        # Verify ownership
        sql_check = "SELECT id FROM chat_sessions WHERE id = CAST(:session_id AS UUID) AND user_id = CAST(:user_id AS UUID)"
        res = await db.execute(text(sql_check), {"session_id": str(session_id), "user_id": str(user_id)})
        if not res.first():
            raise ValueError("Session not found or unauthorized")
            
        sql_hist = "SELECT id, role, content, created_at FROM chat_messages WHERE session_id = CAST(:session_id AS UUID) ORDER BY created_at ASC"
        res_hist = await db.execute(text(sql_hist), {"session_id": str(session_id)})
        
        messages = []
        for r in res_hist.all():
            messages.append({
                "id": str(r[0]),
                "role": r[1],
                "content": r[2],
                "created_at": r[3]
            })
            
        return messages

chatbot_service = ChatbotService()
