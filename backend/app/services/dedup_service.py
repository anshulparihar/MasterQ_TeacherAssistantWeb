import hashlib
import re
import asyncio
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import structlog
from app.models.question import Question

logger = structlog.get_logger()

class DeduplicationService:
    SIMILARITY_THRESHOLD = 0.92
    DEDUP_WINDOW_DAYS = 3
    
    async def normalize_question(self, text: str) -> str:
        """
        Normalize question text for hashing:
        - lowercase
        - remove extra whitespace
        - remove punctuation
        - sort MCQ options alphabetically (so reordered options = same question)
        """
        normalized = text.lower()
        normalized = re.sub(r'[^\w\s\n]', '', normalized)
        
        lines = [line.strip() for line in normalized.split('\n') if line.strip()]
        
        # Basic heuristic to sort the last 4 elements alphabetically if they exist (assuming 4 MCQ options)
        if len(lines) >= 5:
            potential_options = lines[-4:]
            potential_options.sort()
            lines = lines[:-4] + potential_options
            
        normalized_str = " ".join(lines)
        normalized_str = re.sub(r'\s+', ' ', normalized_str).strip()
        return normalized_str

    async def compute_hash(self, normalized_text: str) -> str:
        """SHA256 of normalized text → hex string"""
        return hashlib.sha256(normalized_text.encode('utf-8')).hexdigest()

    async def is_duplicate(
        self,
        db: AsyncSession,
        user_id: UUID,
        question_text: str,
        question_embedding: list[float]
    ) -> bool:
        """
        Two-phase deduplication
        """
        normalized = await self.normalize_question(question_text)
        computed_hash = await self.compute_hash(normalized)
        
        # Phase 1 — Exact hash check (fast)
        sql_exact = f"""
        SELECT COUNT(*) FROM questions q
        JOIN question_papers qp ON q.question_paper_id = qp.id
        WHERE qp.user_id = :user_id 
          AND q.question_hash = :hash
          AND q.created_at > NOW() - INTERVAL '{self.DEDUP_WINDOW_DAYS} days'
        """
        result = await db.execute(text(sql_exact), {"user_id": str(user_id), "hash": computed_hash})
        count = result.scalar()
        if count and count > 0:
            logger.info("Deduplication: Phase 1 Exact hash match.")
            return True
            
        # Phase 2 — Semantic similarity check
        vector_str = "[" + ",".join(map(str, question_embedding)) + "]"
        sql_semantic = f"""
        SELECT q.id, 1 - (q.question_embedding <=> CAST(:embedding AS vector)) as similarity
        FROM questions q
        JOIN question_papers qp ON q.question_paper_id = qp.id
        WHERE qp.user_id = :user_id
          AND q.created_at > NOW() - INTERVAL '{self.DEDUP_WINDOW_DAYS} days'
          AND q.question_embedding IS NOT NULL
          AND 1 - (q.question_embedding <=> CAST(:embedding AS vector)) > :threshold
        LIMIT 1
        """
        res2 = await db.execute(text(sql_semantic), {
            "user_id": str(user_id), 
            "embedding": vector_str,
            "threshold": self.SIMILARITY_THRESHOLD
        })
        if res2.first():
            logger.info("Deduplication: Phase 2 Semantic match.")
            return True
            
        return False

    async def filter_duplicates(
        self,
        db: AsyncSession,
        user_id: UUID,
        candidate_questions: list[dict],
        embedding_service
    ) -> list[dict]:
        """
        Filter list of generated questions, removing duplicates.
        Run checks concurrently with semaphore(10)
        """
        semaphore = asyncio.Semaphore(10)
        filtered = []
        
        async def process_candidate(q):
            async with semaphore:
                # 1. Generate embedding
                text_to_embed = q.get('question_text', '')
                if 'options' in q and q['options']:
                    opts = " ".join([o.get('text', '') for o in q['options']])
                    text_to_embed += " " + opts
                    
                embs = await embedding_service.embed_texts([text_to_embed])
                if not embs or len(embs) == 0:
                    return None
                    
                q_emb = embs[0]
                
                # 2. Check duplicate
                is_dup = await self.is_duplicate(db, user_id, text_to_embed, q_emb)
                if not is_dup:
                    q['question_embedding'] = q_emb
                    normalized = await self.normalize_question(text_to_embed)
                    q['question_hash'] = await self.compute_hash(normalized)
                    return q
                return None

        tasks = [process_candidate(q) for q in candidate_questions]
        results = await asyncio.gather(*tasks)
        
        for res in results:
            if res is not None:
                filtered.append(res)
                
        return filtered

    async def store_question_hashes(
        self,
        db: AsyncSession,
        questions: list[Question],
        embedding_service
    ):
        """
        Ensure all stored questions have question_hash and question_embedding set.
        """
        for q in questions:
            if not q.question_hash or not q.question_embedding:
                text_to_embed = q.text
                if q.options:
                    text_to_embed += " " + " ".join(q.options)
                    
                embs = await embedding_service.embed_texts([text_to_embed])
                if embs and len(embs) > 0:
                    q.question_embedding = embs[0]
                    
                normalized = await self.normalize_question(text_to_embed)
                q.question_hash = await self.compute_hash(normalized)
                
        await db.commit()

dedup_service = DeduplicationService()
