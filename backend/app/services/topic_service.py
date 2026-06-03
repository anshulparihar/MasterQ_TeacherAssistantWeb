import asyncio
import json
import uuid
import random
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.config import settings
import google.generativeai as genai
import structlog
from app.models.topic import DocumentTopic

logger = structlog.get_logger()

genai.configure(api_key=settings.GEMINI_API_KEY)

class TopicExtractionService:
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)
        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
    
    async def extract_topics_from_document(
        self, 
        db: AsyncSession,
        document_id: uuid.UUID,
        document_text: str,
        subject_name: str | None
    ) -> list[DocumentTopic]:
        
        # Approximate 8000 tokens ~ 32000 chars limit to prevent heavy context bloat
        if len(document_text) > 32000:
            document_text = document_text[:32000]
            
        subject_context = f"The subject of this document is {subject_name}." if subject_name else "Extract topics from this document."
            
        prompt = f"""
        {subject_context}
        Extract structured hierarchical topics and subtopics from the following document text.
        Return the result strictly as a JSON object matching this schema:
        {{
          "topics": [
            {{
              "topic_name": "String",
              "subtopics": ["String", "String"],
              "importance_score": 0.9
            }}
          ]
        }}
        
        Document Text:
        {document_text}
        """
        
        async with self.semaphore:
            # We use to_thread because Gemini generation config is synchronous under the hood natively
            response = await asyncio.to_thread(
                self.model.generate_content,
                prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
        try:
            result_json = json.loads(response.text)
            topics_data = result_json.get("topics", [])
            
            created_topics = []
            for t in topics_data:
                dt = DocumentTopic(
                    document_id=document_id,
                    topic_name=t.get("topic_name", ""),
                    subtopics=t.get("subtopics", []),
                    importance_score=float(t.get("importance_score", 0.5))
                )
                created_topics.append(dt)
                
            db.add_all(created_topics)
            await db.commit()
            return created_topics
            
        except json.JSONDecodeError as e:
            logger.error("Failed to decode JSON from Gemini", error=str(e), response=response.text)
            return []
        except Exception as e:
            logger.error("Failed to process topics", error=str(e))
            return []
    
    async def get_topics_for_documents(
        self,
        db: AsyncSession,
        document_ids: list[uuid.UUID]
    ) -> list[dict]:
        
        if not document_ids:
            return []
            
        sql = """
        SELECT dt.topic_name, dt.subtopics, dt.document_id, dt.importance_score
        FROM document_topics dt
        WHERE dt.document_id = ANY(CAST(:doc_ids AS uuid[]))
        ORDER BY dt.importance_score DESC
        """
        
        result = await db.execute(
            text(sql), 
            {"doc_ids": [str(d) for d in document_ids]}
        )
        
        topics = []
        for row in result.all():
            topics.append({
                "topic_name": row[0],
                "subtopics": row[1],
                "document_id": str(row[2]),
                "importance_score": float(row[3])
            })
            
        return topics
    
    async def build_topic_context(
        self,
        topics: list[dict],
        selected_doc_topics: list[dict],
        difficulty: str
    ) -> str:
        
        priority_topics = selected_doc_topics
        # Make sure we don't duplicate topics in additional array by filtering on topic_name and doc_id
        selected_keys = {(t['topic_name'], t['document_id']) for t in selected_doc_topics}
        additional_topics = [t for t in topics if (t['topic_name'], t['document_id']) not in selected_keys]
        
        chosen_priority = []
        chosen_additional = []
        
        # Difficulty routing
        if difficulty == 'easy':
            if priority_topics:
                chosen_priority = [random.choice(priority_topics)]
            elif additional_topics:
                chosen_additional = [random.choice(additional_topics)]
                
        elif difficulty == 'medium':
            if priority_topics:
                chosen_priority = random.sample(priority_topics, min(3, len(priority_topics)))
            if not chosen_priority and additional_topics:
                chosen_additional = random.sample(additional_topics, min(2, len(additional_topics)))
                
        elif difficulty == 'hard':
            if priority_topics:
                chosen_priority = random.sample(priority_topics, min(3, len(priority_topics)))
            if additional_topics:
                chosen_additional = random.sample(additional_topics, min(2, len(additional_topics)))
                
        # String rendering
        context_parts = []
        
        if chosen_priority:
            context_parts.append("HIGH PRIORITY TOPICS:")
            for t in chosen_priority:
                sub = ", ".join(t['subtopics'])
                context_parts.append(f"- {t['topic_name']}: {sub}")
                
        if chosen_additional:
            context_parts.append("ADDITIONAL CONTEXT TOPICS:")
            for t in chosen_additional:
                sub = ", ".join(t['subtopics'])
                context_parts.append(f"- {t['topic_name']}: {sub}")
                
        return "\n".join(context_parts)

topic_service = TopicExtractionService()
