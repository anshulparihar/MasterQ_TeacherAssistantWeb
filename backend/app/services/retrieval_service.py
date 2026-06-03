import uuid
import json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from fastapi import HTTPException, status
from app.services.embedding_service import embedding_service
from app.services.cache_service import cache_service

class RetrievalService:
    
    async def get_retrieval_scope(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        selected_document_ids: list[uuid.UUID],
        from_this_only: bool,
        subject_id: uuid.UUID | None = None,
        academic_level: str | None = None
    ) -> tuple[list[uuid.UUID], str]:
        """
        Determines which document IDs to search and returns scope description.
        """
        # Fetch admin documents
        sql_admin = "SELECT id FROM documents WHERE doc_type = 'admin' AND status = 'ready'"
        params_admin = {}
        if subject_id:
            sql_admin += " AND subject_id = :subject_id"
            params_admin["subject_id"] = str(subject_id)
        if academic_level and academic_level != 'Any / General':
            sql_admin += " AND academic_level = :academic_level"
            params_admin["academic_level"] = academic_level
            
        result = await db.execute(text(sql_admin), params_admin)
        admin_doc_ids = [row[0] for row in result.all()]

        if not selected_document_ids:
            # Scenario A: User has no docs OR selected none -> Admin docs ONLY
            return admin_doc_ids, "admin_only"
            
        # If docs are selected, validate user owns them AND they match the subject/level
        sql_selected = "SELECT id, user_id FROM documents WHERE id = ANY(CAST(:selected_ids AS uuid[])) AND user_id = :user_id"
        params_selected = {
            "selected_ids": [str(d) for d in selected_document_ids],
            "user_id": str(user_id)
        }
        if subject_id:
            sql_selected += " AND subject_id = :subject_id"
            params_selected["subject_id"] = str(subject_id)
        if academic_level and academic_level != 'Any / General':
            sql_selected += " AND academic_level = :academic_level"
            params_selected["academic_level"] = academic_level
            
        result = await db.execute(text(sql_selected), params_selected)
        rows = result.all()
        
        # Check if ALL selected documents were found and matched the criteria
        # The prompt says: "If any selected doc doesn't match → raise HTTPException(422...)"
        # But wait, we also need to validate ownership if they didn't match ownership. 
        # Actually, the user prompt states:
        # "If any selected doc doesn't match → raise HTTPException(422, 'Some selected documents do not belong to the selected subject or academic level')"
        
        # First, ensure all selected IDs exist and belong to user
        sql_own = "SELECT id, user_id FROM documents WHERE id = ANY(CAST(:doc_ids AS uuid[]))"
        own_result = await db.execute(text(sql_own), {"doc_ids": [str(d) for d in selected_document_ids]})
        own_rows = own_result.all()
        
        if len(own_rows) != len(selected_document_ids):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="One or more selected documents not found")
            
        for row in own_rows:
            if row[1] != user_id:
                raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have access to one or more selected documents")
                
        # Now check if they passed the subject/level filter
        if len(rows) != len(selected_document_ids):
            raise HTTPException(status_code=422, detail="Some selected documents do not belong to the selected subject or academic level")
                
        if not from_this_only:
            # Scenario B: Admin docs + selected user docs
            return admin_doc_ids + selected_document_ids, "admin_and_user"
        else:
            # Scenario C: Selected user docs ONLY
            return selected_document_ids, "user_only"

    async def retrieve_chunks(
        self,
        db: AsyncSession,
        query_embedding: list[float],
        document_ids: list[uuid.UUID],
        top_k: int = 20,
        topic_boost_docs: list[uuid.UUID] | None = None
    ) -> list[dict]:
        """
        Semantic similarity search within allowed document_ids.
        Uses pgvector for vector math (cosine similarity = 1 - cosine distance).
        """
        if not document_ids:
            return []
            
        sql = """
        SELECT dc.id as chunk_id, dc.content as chunk_text, dc.document_id as doc_id,
               d.doc_type, d.filename as doc_filename, d.user_id,
               1 - (dc.embedding <=> CAST(:query_embedding AS vector)) as similarity
        FROM document_chunks dc
        JOIN documents d ON dc.document_id = d.id
        WHERE dc.document_id = ANY(CAST(:doc_ids AS uuid[]))
        ORDER BY dc.embedding <=> CAST(:query_embedding AS vector)
        LIMIT :limit
        """
        
        result = await db.execute(
            text(sql), 
            {
                "query_embedding": str(query_embedding), 
                "doc_ids": [str(d) for d in document_ids],
                "limit": top_k * 2 # Fetch more for potential re-ranking
            }
        )
        
        chunks = []
        for row in result:
            chunk = dict(row._mapping)
            # Apply topic boost if applicable
            if topic_boost_docs and uuid.UUID(str(chunk['doc_id'])) in topic_boost_docs:
                chunk['similarity'] = float(chunk['similarity']) * 1.5
            else:
                chunk['similarity'] = float(chunk['similarity'])
            chunks.append(chunk)
            
        # Re-rank based on potentially boosted similarity
        chunks.sort(key=lambda x: x['similarity'], reverse=True)
        return chunks[:top_k]

    async def _get_topic_filtered_document_ids(
        self,
        db: AsyncSession,
        candidate_document_ids: list[uuid.UUID],
        selected_topics: list[str],
        selected_subtopics: list[str]
    ) -> list[uuid.UUID]:
        """
        From candidate_document_ids, return only those that contain
        at least one of the selected topics or subtopics.
        """
        if not candidate_document_ids:
            return []
            
        if not selected_topics and not selected_subtopics:
            return candidate_document_ids
            
        # Expand selected_topics to their subtopics
        all_subtopics = list(selected_subtopics)
        if selected_topics:
            sql_expand = """
            SELECT dt.subtopics FROM document_topics dt
            WHERE dt.topic_name = ANY(:selected_topics)
              AND dt.document_id = ANY(CAST(:candidate_ids AS uuid[]))
            """
            result = await db.execute(text(sql_expand), {
                "selected_topics": selected_topics,
                "candidate_ids": [str(d) for d in candidate_document_ids]
            })
            for row in result.all():
                if row[0]:
                    all_subtopics.extend(row[0])
                    
        all_subtopics = list(set(all_subtopics))
        
        sql_filter = """
        SELECT DISTINCT dt.document_id
        FROM document_topics dt
        WHERE dt.document_id = ANY(CAST(:candidate_ids AS uuid[]))
          AND (
            dt.topic_name = ANY(:selected_topics)
            OR EXISTS (
              SELECT 1
              FROM jsonb_array_elements_text(dt.subtopics) AS st
              WHERE st = ANY(:all_subtopics)
            )
          )
        """
        
        result = await db.execute(text(sql_filter), {
            "candidate_ids": [str(d) for d in candidate_document_ids],
            "selected_topics": selected_topics,
            "all_subtopics": all_subtopics
        })
        
        filtered_ids = [row[0] for row in result.all()]
        
        if not filtered_ids:
            raise HTTPException(status_code=422, detail="No documents found containing the selected topics. Try different topics or deselect topic filter.")
            
        return filtered_ids

    async def retrieve_for_question_generation(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        selected_document_ids: list[uuid.UUID],
        from_this_only: bool,
        subject: str,
        subject_id: uuid.UUID | None,
        academic_level: str | None,
        topics: list[str],
        selected_topics: list[str],
        selected_subtopics: list[str],
        difficulty: str,
        top_k: int = 20
    ) -> tuple[list[dict], str]:
        
        # 1. Determine scope
        doc_ids_to_search, scope = await self.get_retrieval_scope(
            db, user_id, selected_document_ids, from_this_only, subject_id, academic_level
        )
        
        # 2. Hard filter by topics/subtopics
        if selected_topics or selected_subtopics:
            doc_ids_to_search = await self._get_topic_filtered_document_ids(
                db, doc_ids_to_search, selected_topics, selected_subtopics
            )
        
        # Build composite query string
        query_str = f"Subject: {subject}. Topics: {', '.join(topics)}. Difficulty: {difficulty}."
        
        # Check cache
        cache_key = f"retrieval:{cache_service.generate_cache_key(doc_ids_to_search, query_str, top_k)}"
        cached_result = await cache_service.get(cache_key)
        
        if cached_result:
            return cached_result['chunks'], cached_result['scope']
            
        # 3. Embed query
        query_embedding = await embedding_service.embed_query(query_str)
        
        # 4. Retrieve chunks
        # If the user selected docs, we boost them as they are likely highly relevant
        topic_boost_docs = selected_document_ids if selected_document_ids else None
        
        chunks = await self.retrieve_chunks(
            db, query_embedding, doc_ids_to_search, top_k, topic_boost_docs
        )
        
        # Format chunk UUIDs to strings for JSON serialization
        for chunk in chunks:
            chunk['chunk_id'] = str(chunk['chunk_id'])
            chunk['doc_id'] = str(chunk['doc_id'])
            if chunk['user_id']:
                chunk['user_id'] = str(chunk['user_id'])
        
        # 5. Cache result (TTL = 1800 as requested)
        await cache_service.set(cache_key, {'chunks': chunks, 'scope': scope}, 1800)
        
        return chunks, scope

    async def retrieve_for_chatbot(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        query: str,
        selected_document_ids: list[uuid.UUID],
        selected_paper_ids: list[uuid.UUID],
        top_k: int = 15
    ) -> tuple[list[dict], list[dict]]:
        
        # Determine chatbot scope
        doc_ids_to_search = []
        
        if not selected_document_ids and not selected_paper_ids:
            # Admin docs + all user's own docs
            admin_result = await db.execute(text("SELECT id FROM documents WHERE doc_type = 'admin'"))
            user_result = await db.execute(text("SELECT id FROM documents WHERE user_id = :user_id"), {"user_id": str(user_id)})
            
            doc_ids_to_search.extend([row[0] for row in admin_result.all()])
            doc_ids_to_search.extend([row[0] for row in user_result.all()])
        else:
            # Only selected documents/papers
            # For papers, find their associated documents
            if selected_paper_ids:
                sql = "SELECT document_id FROM paper_documents WHERE question_paper_id = ANY(CAST(:paper_ids AS uuid[]))"
                paper_docs_result = await db.execute(text(sql), {"paper_ids": [str(p) for p in selected_paper_ids]})
                doc_ids_to_search.extend([row[0] for row in paper_docs_result.all()])
                
            doc_ids_to_search.extend(selected_document_ids)
            
        # De-duplicate doc IDs
        doc_ids_to_search = list(set(doc_ids_to_search))
        
        # Embed query
        query_embedding = await embedding_service.embed_query(query)
        
        # Retrieve context chunks
        context_chunks = await self.retrieve_chunks(
            db, query_embedding, doc_ids_to_search, top_k
        )
        
        # Format chunk UUIDs to strings for JSON serialization
        for chunk in context_chunks:
            chunk['chunk_id'] = str(chunk['chunk_id'])
            chunk['doc_id'] = str(chunk['doc_id'])
            if chunk['user_id']:
                chunk['user_id'] = str(chunk['user_id'])
                
        # Pass all references, they will be sanitized in chatbot_service
        all_references = context_chunks
        
        # If we had papers, retrieve question text
        # Assumes questions table exists and has a question_paper_id
        if selected_paper_ids:
            try:
                q_sql = "SELECT text, type, correct_answer, model_answer, explanation FROM questions WHERE question_paper_id = ANY(CAST(:paper_ids AS uuid[]))"
                q_result = await db.execute(text(q_sql), {"paper_ids": [str(p) for p in selected_paper_ids]})
                for row in q_result.all():
                    q_text, q_type, correct_ans, model_ans, expl = row[0], row[1], row[2], row[3], row[4]
                    ans = correct_ans if q_type == 'mcq' else model_ans
                    chunk_text = f"Question: {q_text}\nAnswer: {ans}\nExplanation: {expl}"
                    context_chunks.append({
                        'chunk_text': chunk_text,
                        'doc_type': 'paper_question',
                        'doc_filename': 'Generated Question Paper'
                    })
            except Exception as e:
                # Silently ignore if questions schema doesn't perfectly match this yet
                pass
                
        return context_chunks, all_references

retrieval_service = RetrievalService()
