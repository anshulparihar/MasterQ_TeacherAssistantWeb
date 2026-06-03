import hashlib
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from app.services.embedding_service import embedding_service
import structlog

logger = structlog.get_logger()

class DeduplicationService:
    async def is_duplicate(self, db: AsyncSession, user_id: UUID, question_text: str) -> bool:
        """
        Check question deduplication for the last 3 days per user via:
        1. Exact SHA256 hash match (fast path)
        2. Cosine similarity > 0.92 on question_embedding (semantic path)
        """
        # 1. Exact Match
        q_hash = hashlib.sha256(question_text.encode('utf-8')).hexdigest()
        
        sql_exact = """
        SELECT q.id FROM questions q
        JOIN question_papers qp ON q.question_paper_id = qp.id
        WHERE qp.user_id = :user_id 
        AND q.question_hash = :hash
        AND q.created_at >= NOW() - INTERVAL '3 days'
        LIMIT 1
        """
        result = await db.execute(text(sql_exact), {"user_id": str(user_id), "hash": q_hash})
        if result.first():
            logger.info("Deduplication: Exact hash match found.")
            return True
            
        # 2. Semantic Match
        try:
            embs = await embedding_service.embed_texts([question_text])
            if embs and len(embs) > 0:
                emb = embs[0]
                vector_str = "[" + ",".join(map(str, emb)) + "]"
                
                sql_semantic = """
                SELECT q.id FROM questions q
                JOIN question_papers qp ON q.question_paper_id = qp.id
                WHERE qp.user_id = :user_id
                AND q.created_at >= NOW() - INTERVAL '3 days'
                AND q.question_embedding IS NOT NULL
                AND 1 - (q.question_embedding <=> CAST(:embedding AS vector)) > 0.92
                LIMIT 1
                """
                res2 = await db.execute(text(sql_semantic), {"user_id": str(user_id), "embedding": vector_str})
                if res2.first():
                    logger.info("Deduplication: Semantic match > 0.92 found.")
                    return True
        except Exception as e:
            logger.error(f"Semantic deduplication check failed: {e}")
            
        return False

deduplication_service = DeduplicationService()
