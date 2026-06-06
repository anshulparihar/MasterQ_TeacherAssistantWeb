import asyncio
import json
import hashlib
import math
import uuid
import time
from typing import List, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
import google.generativeai as genai
import structlog
from fastapi import HTTPException
from app.config import settings
from app.services.retrieval_service import retrieval_service
from app.services.topic_service import topic_service
from app.services.dedup_service import dedup_service
from app.services.storage_service import storage_service
from app.services.diagram_service import diagram_service
from app.services.cache_service import cache_service
from app.models.document import Document

logger = structlog.get_logger()
genai.configure(api_key=settings.GEMINI_API_KEY)

class QuestionGenerationEngine:
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)

        self.model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        self.retrieval_service = retrieval_service
        self.topic_service = topic_service
        self.dedup_service = dedup_service

    def _calculate_question_counts(
        self,
        total: int,
        distribution: dict
    ) -> dict[str, int]:
        """
        Distribute total questions across difficulties without overshoot.
        Uses largest-remainder method (standard rounding algorithm).
        """
        difficulties = ['easy', 'medium', 'hard']
        
        # Step 1: compute exact (fractional) counts
        exact = {d: total * distribution[d] for d in difficulties}
        
        # Step 2: floor everything
        floored = {d: int(exact[d]) for d in difficulties}
        
        # Step 3: compute remainders
        remainders = {d: exact[d] - floored[d] for d in difficulties}
        
        # Step 4: how many extra 1s do we need to distribute?
        total_so_far = sum(floored.values())
        extras_needed = total - total_so_far  # always 0, 1, or 2
        
        # Step 5: give extras to difficulties with largest remainders
        sorted_by_remainder = sorted(difficulties, key=lambda d: remainders[d], reverse=True)
        for i in range(extras_needed):
            floored[sorted_by_remainder[i]] += 1
        
        # Guarantee minimum 1 per difficulty if total >= 3
        if total >= 3:
            for d in difficulties:
                if floored[d] == 0:
                    # Take from the difficulty with most questions
                    largest = max(difficulties, key=lambda x: floored[x])
                    if floored[largest] > 1:
                        floored[largest] -= 1
                        floored[d] = 1
        
        return floored  # Always sums exactly to total

    async def generate_paper(
        self,
        db: AsyncSession,
        user_id: uuid.UUID,
        request: dict
    ) -> dict:
        start_time = time.time()
        
        # 1. Check Redis cache
        req_hash = hashlib.md5(json.dumps(request, sort_keys=True, default=str).encode()).hexdigest()
        cache_key = f"qgen:{user_id}:{req_hash}"
        logger.info(f"cache_key: {cache_key}, user_id={user_id}")
        cached_res = await cache_service.get(cache_key)
        if cached_res:
            logger.info(f"Returning cached generation result for {user_id}", duration_sec=round(time.time() - start_time, 2))
            return cached_res
            
        doc_ids = request.get('document_ids', request.get('selected_document_ids', []))

        # FIX 2: Selected documents status='ready' check
        if doc_ids:
            # Fetch status of all selected documents
            parsed_doc_ids = [uuid.UUID(str(d)) for d in doc_ids]
            result = await db.execute(
                select(Document.id, Document.status, Document.user_id)
                .where(Document.id.in_(parsed_doc_ids))
            )
            docs = result.fetchall()
            
            # Check all exist
            found_ids = {row.id for row in docs}
            missing = set(parsed_doc_ids) - found_ids
            if missing:
                raise HTTPException(404, f"Documents not found: {missing}")
            
            # Check ownership (user can only select their own docs)
            not_owned = [row.id for row in docs if str(row.user_id) != str(user_id)]
            if not_owned:
                raise HTTPException(403, "You do not own some of the selected documents")
            
            # Check all are ready
            not_ready = [row.id for row in docs if row.status != 'ready']
            if not_ready:
                raise HTTPException(422, 
                    f"{len(not_ready)} document(s) are still processing or failed. "
                    "Wait for processing to complete before generating questions.")

        # 2. Fetch exam type guidelines from DB
        sql_exam = "SELECT name, guidelines, few_shot_examples FROM exam_types WHERE id = :id"
        exam_res = await db.execute(text(sql_exam), {"id": request['exam_type_id']})
        exam_row = exam_res.first()
        if not exam_row:
            raise ValueError("Invalid exam_type_id")
        exam_name, exam_guidelines, exam_few_shot = exam_row[0], exam_row[1], exam_row[2]

        # 3. Fetch subject info from DB
        sql_sub = "SELECT name FROM subjects WHERE id = :id"
        sub_res = await db.execute(text(sql_sub), {"id": request['subject_id']})
        sub_row = sub_res.first()
        subject_name = sub_row[0] if sub_row else "General Subject"

        # 4. Retrieve context chunks using the new retrieve_for_question_generation method
        selected_doc_ids = [uuid.UUID(str(d)) for d in doc_ids]
        
        chunks, scope = await self.retrieval_service.retrieve_for_question_generation(
            db=db,
            user_id=user_id,
            selected_document_ids=selected_doc_ids,
            from_this_only=request.get('from_this_only', False),
            subject=subject_name,
            subject_id=uuid.UUID(str(request.get('subject_id'))) if request.get('subject_id') else None,
            academic_level=request.get('academic_level', 'High School'),
            topics=request.get('topics', []),
            selected_topics=request.get('selected_topics', []),
            selected_subtopics=request.get('selected_subtopics', []),
            difficulty="mixed",  # A general retrieval for the whole paper
            top_k=20
        )
        
        if not chunks:
            logger.info("No context material found for the given parameters. Relying on LLM general knowledge.")
            
        chunk_texts = [c['chunk_text'] for c in chunks] # retrieve_chunks returns dict with 'chunk_text'
        joined_chunks = "\n\n---\n\n".join(chunk_texts)

        # 5. Extract topics from retrieved docs
        retrieved_doc_ids = list(set([uuid.UUID(str(c['doc_id'])) for c in chunks]))
        topics = await self.topic_service.get_topics_for_documents(db, retrieved_doc_ids)

        selected_ids_str = {str(d) for d in selected_doc_ids}
        selected_doc_topics = [t for t in topics if str(t.get('document_id', '')) in selected_ids_str]
        other_topics = [t for t in topics if str(t.get('document_id', '')) not in selected_ids_str]

        # 6. Calculate question counts per difficulty per type (FIX 3 Applied)
        # Using exact counts provided by the new request schema
        mcq_counts = {
            "easy": request.get('mcq_easy', 0),
            "medium": request.get('mcq_medium', 0),
            "hard": request.get('mcq_hard', 0)
        }
        
        theory_counts = {
            "easy": request.get('theory_easy', 0),
            "medium": request.get('theory_medium', 0),
            "hard": request.get('theory_hard', 0)
        }
        
        batches = []
        for q_type, counts in [('mcq', mcq_counts), ('theory', theory_counts)]:
            total_type = sum(counts.values())
            if total_type == 0:
                continue
                
            total_rec = max(1, math.ceil(total_type * 0.20))
            
            rec_assigned = {diff: 0 for diff in ['easy', 'medium', 'hard']}
            available_buckets = [d for d in ['easy', 'medium', 'hard'] if counts.get(d, 0) > 0]
            
            if available_buckets:
                for i in range(total_rec):
                    rec_assigned[available_buckets[i % len(available_buckets)]] += 1
            else:
                rec_assigned["medium"] = total_rec

            for diff in ['easy', 'medium', 'hard']:
                count = counts.get(diff, 0)
                rec_count = rec_assigned.get(diff, 0)
                if count > 0 or rec_count > 0:
                    target_count = count + rec_count
                    
                    batches.append({
                        "type": q_type,
                        "difficulty": diff,
                        "base_count": count,
                        "target_count": target_count
                    })

        # 7. For each (type, difficulty) combination, generate questions in parallel
        tasks = []
        for batch in batches:
            topic_context = await self.topic_service.build_topic_context(other_topics, selected_doc_topics, batch['difficulty'])
            tasks.append(
                self._generate_questions_batch(
                    chunk_texts, topic_context, exam_name, exam_guidelines, exam_few_shot,
                    subject_name, request.get('academic_level', 'High School'), 
                    batch['type'], batch['difficulty'], batch['target_count'], user_id,
                    request.get('selected_topics', []), request.get('selected_subtopics', [])
                )
            )
            
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        all_generated_questions = []
        for i, res in enumerate(results):
            if isinstance(res, Exception):
                logger.error(f"Batch generation failed: {res}")
                continue
            all_generated_questions.extend(res)

        # 8. Run deduplication on all generated questions
        from app.services.embedding_service import embedding_service
        valid_questions = await self.dedup_service.filter_duplicates(
            db=db,
            user_id=user_id,
            candidate_questions=all_generated_questions,
            embedding_service=embedding_service
        )
        
        # Diagram injection via batch detection to save API rate limits
        diagram_needs = await diagram_service.detect_diagram_need_batch(
            questions=valid_questions,
            subject=subject_name
        )
        
        processed_questions = []
        for i, q in enumerate(valid_questions):
            detection = diagram_needs[i] if i < len(diagram_needs) else {'needs_diagram': False}
            if detection.get('needs_diagram'):
                diag_url = await diagram_service.generate_diagram_and_upload(
                    question_text=q['question_text'],
                    detection=detection,
                    storage_service=storage_service,
                    user_id=str(user_id)
                )
                if diag_url:
                    q['diagram_url'] = diag_url
                    q['diagram_type'] = 'auto_generated'
            processed_questions.append(q)
            
        valid_questions = processed_questions

        # 9. Split into main questions + recommendations based on original counts
        main_qs = []
        rec_qs = []
        
        bucket_counts = {f"{b['type']}_{b['difficulty']}": 0 for b in batches}
        bucket_limits = {f"{b['type']}_{b['difficulty']}": b['base_count'] for b in batches}
        
        for q in valid_questions:
            key = f"{q.get('question_type')}_{q.get('difficulty')}"
            if bucket_counts.get(key, 0) < bucket_limits.get(key, 0):
                main_qs.append(q)
                if key in bucket_counts:
                    bucket_counts[key] += 1
            else:
                rec_qs.append(q)

        # 10. Create QuestionPaper record + Question records in DB
        paper_id = uuid.uuid4()
        
        sql_paper = """
        INSERT INTO question_papers (id, title, user_id, subject_id, exam_type_id, created_at)
        VALUES (:id, :title, :user_id, :subject_id, :exam_type_id, NOW())
        """
        await db.execute(text(sql_paper), {
            "id": str(paper_id),
            "title": f"Generated Paper - {subject_name}",
            "user_id": str(user_id),
            "subject_id": str(request['subject_id']),
            "exam_type_id": str(request['exam_type_id'])
        })
        
        # Link documents
        for doc_id in set([c['doc_id'] for c in chunks]):
            sql_link = "INSERT INTO paper_documents (question_paper_id, document_id) VALUES (:qid, :did) ON CONFLICT DO NOTHING"
            await db.execute(text(sql_link), {"qid": str(paper_id), "did": str(doc_id)})
        
        # Fetch fallback topic
        sql_fallback_topic = "SELECT id FROM topics WHERE subject_id = :subject_id LIMIT 1"
        fallback_topic_res = await db.execute(text(sql_fallback_topic), {"subject_id": str(request['subject_id'])})
        fallback_topic_row = fallback_topic_res.first()
        fallback_topic_id = str(fallback_topic_row[0]) if fallback_topic_row else None

        topic_cache = {}
        async def get_or_create_topic(topic_name: str) -> str:
            if not topic_name:
                return fallback_topic_id
                
            topic_name = str(topic_name).strip()
            if topic_name in topic_cache:
                return topic_cache[topic_name]
            
            sql_check = "SELECT id FROM topics WHERE LOWER(name) = LOWER(:name) AND subject_id = :subject_id"
            res = await db.execute(text(sql_check), {"name": topic_name, "subject_id": str(request['subject_id'])})
            row = res.first()
            if row:
                topic_cache[topic_name] = str(row[0])
                return str(row[0])
            
            try:
                async with db.begin_nested():
                    new_id = str(uuid.uuid4())
                    sql_insert = "INSERT INTO topics (id, name, subject_id, created_at) VALUES (:id, :name, :subject_id, NOW())"
                    await db.execute(text(sql_insert), {"id": new_id, "name": topic_name, "subject_id": str(request['subject_id'])})
                    topic_cache[topic_name] = new_id
                    return new_id
            except Exception:
                res = await db.execute(text(sql_check), {"name": topic_name, "subject_id": str(request['subject_id'])})
                row = res.first()
                if row:
                    topic_cache[topic_name] = str(row[0])
                    return str(row[0])
                return fallback_topic_id

        async def insert_questions(q_list, is_rec):
            for q in q_list:
                sql_q = """
                INSERT INTO questions (id, text, type, options, correct_answer, model_answer, 
                difficulty, topic_id, question_paper_id, diagram_url, diagram_type, explanation, hint, marks, is_recommendation, question_hash, question_embedding, created_at)
                VALUES (:id, :text, :type, :options, :correct_answer, :model_answer,
                :difficulty, :topic_id, :qp_id, :diagram_url, :diagram_type, :explanation, :hint, :marks, :is_recommendation, :q_hash, :q_embedding, NOW())
                """
                q_id = uuid.uuid4()
                q['id'] = str(q_id)
                opts = [o['text'] for o in q.get('options', [])] if q.get('question_type') == 'mcq' else None
                ans = q.get('answer', '')
                
                emb = q.get('question_embedding')
                pg_vector_str = f"[{','.join(map(str, emb))}]" if emb else None
                
                topics_covered = q.get('topics_covered', [])
                primary_topic_name = topics_covered[0] if topics_covered else None
                q_topic_id = await get_or_create_topic(primary_topic_name)
                
                await db.execute(text(sql_q), {
                    "id": str(q_id),
                    "text": q['question_text'],
                    "type": q['question_type'],
                    "options": opts,
                    "correct_answer": ans if q.get('question_type') == 'mcq' else None,
                    "model_answer": ans if q.get('question_type') == 'theory' else None,
                    "difficulty": q['difficulty'],
                    "topic_id": q_topic_id,
                    "qp_id": str(paper_id),
                    "diagram_url": q.get('diagram_url'),
                    "diagram_type": q.get('diagram_type'),
                    "explanation": q.get('explanation'),
                    "hint": q.get('hint'),
                    "marks": q.get('marks'),
                    "is_recommendation": is_rec,
                    "q_hash": q.get('question_hash'),
                    "q_embedding": pg_vector_str
                })

        await insert_questions(main_qs, False)
        await insert_questions(rec_qs, True)
            
        await db.commit()

        # 11. Cache result
        response_dict = {
            "paper_id": str(paper_id),
            "main_questions": main_qs,
            "recommendations": rec_qs
        }
        await cache_service.set(cache_key, response_dict, ttl=3600)
        
        # 12. Return QuestionPaperResponse
        duration_sec = time.time() - start_time
        logger.info("question_generation_completed", user_id=str(user_id), paper_id=str(paper_id), main_questions=len(main_qs), recommended_questions=len(rec_qs), duration_sec=round(duration_sec, 2))
        return response_dict

    async def _generate_questions_batch(
        self,
        context_chunks: List[str],
        topic_context: str,
        exam_name: str,
        exam_guidelines: Any,
        exam_few_shot: Any,
        subject_name: str,
        academic_level: str,
        question_type: str,
        difficulty: str,
        count: int,
        user_id: uuid.UUID,
        selected_topics: List[str] = [],
        selected_subtopics: List[str] = []
    ) -> List[Dict[str, Any]]:
        
        joined_chunk_texts = "\n\n---\n\n".join(context_chunks)
        marks = await self._calculate_marks(exam_guidelines, question_type, difficulty)
        
        topic_filter_instructions = ""
        if selected_topics or selected_subtopics:
            topic_filter_instructions = f"""
STRICT TOPIC FILTERING REQUIRED:
You MUST ONLY generate questions related to the following selected topics and subtopics:
Selected Topics: {json.dumps(selected_topics)}
Selected Subtopics: {json.dumps(selected_subtopics)}
Do NOT generate general questions. All generated questions must fall within these specific topics/subtopics.
"""

        few_shot_instructions = ""
        if exam_few_shot:
            few_shot_instructions = f"""
PREVIOUS YEAR EXAMPLES (FEW-SHOT ANCHORING):
Analyze these examples from past papers to strictly anchor your generated questions' complexity, length, structure, and tone:
{json.dumps(exam_few_shot)}
"""
        
        json_format = f"""
{{
  "questions": [
    {{
      "question_text": "...",
      "question_type": "{question_type}",
      "difficulty": "{difficulty}",
      "marks": {marks},
      "topics_covered": ["topic1", "topic2"],"""

        if question_type.lower() == 'mcq':
            json_format += """
      "options": [
        {"key": "A", "text": "...", "is_correct": false},
        {"key": "B", "text": "...", "is_correct": true},
        {"key": "C", "text": "...", "is_correct": false},
        {"key": "D", "text": "...", "is_correct": false}
      ],
      "answer": "B","""
        else:
            json_format += """
      "answer": "Detailed, step-by-step descriptive model answer here","""

        json_format += """
      "explanation": "...",
      "hint": "..."
    }
  ]
}"""

        prompt = f"""
You are an expert question paper setter for {exam_name} examination.
Subject: {subject_name}, Academic Level: {academic_level}
{topic_filter_instructions}

EXAM TYPE GUIDELINES:
{json.dumps(exam_guidelines)}
{few_shot_instructions}

TOPIC CONTEXT:
{topic_context}

CONTEXT MATERIAL:
{joined_chunk_texts}

TASK: Generate exactly {count} {question_type.upper()} questions at {difficulty.upper()} difficulty level.

DIFFICULTY RULES:
- EASY: Question must test knowledge of a SINGLE topic/subtopic only
- MEDIUM: Question must integrate 2-3 related topics/subtopics  
- HARD: Question must require reasoning across MULTIPLE topics/subtopics

QUESTION REQUIREMENTS:
- Questions must test CONCEPTUAL understanding, not memorization
- All questions must be strictly based on the provided context material
- For MCQ: provide exactly 4 options (A, B, C, D), only one correct
- Questions must match the style, depth and complexity of {exam_name} previous year papers
- Marks per question: {marks}

MATH FORMATTING:
- ALL mathematical equations, formulas, units (e.g., kg m^2 s^-2), variables, and numbers MUST be formatted using standard LaTeX wrapped in single `$` for inline math (e.g., $s = ut + \\\\frac{{1}}{{2}}at^2$, $E = m(v/c)^n$, $1 \\\\text{{ kg m}}^2 \\\\text{{ s}}^{{-2}}$) or double `$$` for block equations.
- CRITICAL JSON ESCAPING: Because you are outputting JSON, you MUST double-escape all LaTeX backslashes (e.g., use \\\\frac instead of \\frac).
- Do NOT use plain text formats like `at^2`.
- Do NOT use backticks or markdown coloring (like 'marked in red') for math.

CRITICAL: Generate questions ONLY from the provided context. Do not use outside knowledge.

Return ONLY valid JSON in this exact format:
{json_format}
"""
        for attempt in range(2):
            async with self.semaphore:
                try:
                    response = await asyncio.to_thread(
                        self.model.generate_content,
                        prompt,
                        generation_config=genai.GenerationConfig(response_mime_type="application/json")
                    )
                    raw_text = response.text
                    import re
                    match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
                    if match:
                        raw_text = match.group(1)
                    else:
                        start = raw_text.find('{')
                        end = raw_text.rfind('}')
                        if start != -1 and end != -1:
                            raw_text = raw_text[start:end+1]

                    try:
                        data = json.loads(raw_text)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Batch generation parse failure (attempt {attempt+1}): {e}")
                        # Fix common LLM unescaped backslash issues in JSON
                        fixed_text = re.sub(r'\\(?=[^"\\\\/bfnrtu])', r'\\\\', raw_text)
                        try:
                            data = json.loads(fixed_text)
                        except json.JSONDecodeError as e2:
                            if attempt == 1:
                                raise e2
                            continue

                    questions = data.get("questions", [])
                    
                    # FIX 4: MCQ answer validation
                    validated = []
                    for q in questions:
                        if q['question_type'] == 'mcq':
                            options = q.get('options', [])
                            
                            # Must have exactly 4 options
                            if len(options) != 4:
                                logger.warning(f"MCQ has {len(options)} options, expected 4. Discarding.")
                                continue
                            
                            # Must have exactly 1 correct answer
                            correct_count = sum(1 for o in options if o.get('is_correct', False))
                            if correct_count == 0:
                                logger.warning("MCQ has no correct answer. Discarding.")
                                continue
                            if correct_count > 1:
                                logger.warning(f"MCQ has {correct_count} correct answers. Keeping first only.")
                                first_correct_found = False
                                for o in options:
                                    if o.get('is_correct'):
                                        if first_correct_found:
                                            o['is_correct'] = False
                                        else:
                                            first_correct_found = True
                            
                            # Ensure the "answer" field is set to the text of the correct option for insertion
                            correct_opt = next((o for o in options if o.get('is_correct', False)), None)
                            if correct_opt:
                                q['answer'] = correct_opt.get('text', '')
                        
                        validated.append(q)
                    
                    # If we lost too many to validation, log it
                    discarded = len(questions) - len(validated)
                    if discarded > 0:
                        logger.warning(f"Discarded {discarded} invalid questions from batch")
                    
                    return validated

                except Exception as e:
                    logger.warning(f"Batch generation parse failure (attempt {attempt+1}): {e}")
                    
        return []

    async def _calculate_marks(
        self,
        exam_guidelines: Any,
        question_type: str,
        difficulty: str
    ) -> float:
        try:
            if isinstance(exam_guidelines, dict) and question_type in exam_guidelines:
                if difficulty in exam_guidelines[question_type]:
                    return float(exam_guidelines[question_type][difficulty])
        except Exception:
            pass

        # Fallback simplistic logic
        if question_type == 'mcq':
            return 1.0 if difficulty == 'easy' else (2.0 if difficulty == 'medium' else 4.0)
        else:
            return 3.0 if difficulty == 'easy' else (5.0 if difficulty == 'medium' else 10.0)

question_generator = QuestionGenerationEngine()
