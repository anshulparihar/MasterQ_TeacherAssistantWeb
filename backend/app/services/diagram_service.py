import io
import json
import asyncio
from uuid import uuid4
import structlog
from pathlib import Path
import google.generativeai as genai
from app.config import settings

# Imports for our new modules
from app.services.diagram_primitives import PRIMITIVE_REGISTRY, PRIMITIVE_CATALOG, _placeholder_png
from app.services.code_executor import execute_diagram_code, CodeValidationError, CodeExecutionTimeout, CodeExecutionError
from app.schemas.diagram import DiagramGenerationResponse

logger = structlog.get_logger(__name__)
genai.configure(api_key=settings.GEMINI_API_KEY)

class DiagramGenerationService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)
        # Use main model for detection, dedicated model for diagram generation
        self.gemini = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
        self.diagram_gemini = genai.GenerativeModel(settings.DIAGRAM_MODEL_NAME)
        
    async def detect_diagram_need_batch(
        self,
        questions: list[dict],
        subject: str
    ) -> list[dict]:
        """Batched diagram detection to avoid hitting rate limits."""
        if not questions:
            return []
            
        questions_json = json.dumps([{
            "id": i, 
            "text": q.get('question_text'), 
            "type": q.get('question_type')
        } for i, q in enumerate(questions)])
        
        prompt = f"""Subject: {subject}
Here is a list of questions:
{questions_json}

For each question, determine if it REQUIRES a diagram/figure to be clear and answerable.
Only say yes if the question explicitly mentions a diagram, or if it is impossible to understand without one.

Return JSON ONLY. It MUST be a JSON array of objects, one for each question. YOU MUST INCLUDE THE 'id' exactly as provided:
[
  {{
    "id": <id_number>,
    "needs_diagram": true/false,
    "diagram_description": "Detailed description of what to draw, including all labels, values, and visual layout. Be very specific."
  }}
]
"""
        
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.gemini.generate_content,
                    prompt,
                    generation_config=genai.GenerationConfig(response_mime_type="application/json")
                )
                raw_text = response.text
                import re
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1)
                else:
                    start = raw_text.find('[')
                    end = raw_text.rfind(']')
                    if start != -1 and end != -1:
                        raw_text = raw_text[start:end+1]
                        
                results = json.loads(raw_text)
                
                final_results = [{'needs_diagram': False} for _ in questions]
                if isinstance(results, list):
                    for res in results:
                        if isinstance(res, dict) and 'id' in res:
                            idx = res['id']
                            if 0 <= idx < len(questions):
                                final_results[idx] = res
                    return final_results
                else:
                    logger.error(f"Batch diagram detection returned non-list")
                    return final_results
            except Exception as e:
                logger.error(f"Failed to detect diagram needs: {e}")
                return [{'needs_diagram': False} for _ in questions]

    async def _generate_diagram_bytes(self, description: str, question_text: str, retry_error: str = None) -> bytes:
        prompt = f"""
You are an expert educational diagram generator.
Your task is to generate a diagram based on this description and context.

Question Context:
{question_text}

Diagram Description:
{description}

We have a library of pre-built "primitives" that you can use, OR you can write custom Python code using matplotlib.

STRATEGY:
1. If the diagram perfectly matches one of the primitives below, set strategy to "primitive", provide the "primitive_name", and fill "primitive_params".
2. If the diagram is too custom and doesn't fit a primitive, set strategy to "code" and provide "python_code" using matplotlib.

PRIMITIVE CATALOG:
{PRIMITIVE_CATALOG}

If using "code" strategy, follow these rules:
- Provide ONLY the Python code in the "python_code" field (as a string).
- Do NOT use `plt.show()`.
- Define a matplotlib Figure using `fig = plt.figure(...)` or `fig, ax = plt.subplots(...)`. The executor will capture the `fig` variable.
- You can import numpy as np, math, and matplotlib.pyplot as plt.
- Do NOT attempt to read files, use network, or execute shell commands.

Return JSON ONLY in this format:
{{
    "strategy": "primitive" or "code",
    "primitive_name": "...", 
    "primitive_params": {{}},
    "python_code": "..."
}}
"""
        if retry_error:
            prompt += f"\n\nYOUR PREVIOUS ATTEMPT FAILED WITH ERROR:\n{retry_error}\nPlease fix the issue and try again."

        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.diagram_gemini.generate_content,
                    prompt,
                    generation_config=genai.GenerationConfig(response_mime_type="application/json")
                )
                
                raw_text = response.text
                import re
                match = re.search(r'```(?:json)?\s*(.*?)\s*```', raw_text, re.DOTALL)
                if match:
                    raw_text = match.group(1)
                
                data = json.loads(raw_text)
                strategy = data.get("strategy")
                
                if strategy == "primitive":
                    p_name = data.get("primitive_name")
                    p_params = data.get("primitive_params", {})
                    if p_name in PRIMITIVE_REGISTRY:
                        return await asyncio.to_thread(PRIMITIVE_REGISTRY[p_name], p_params)
                    else:
                        raise ValueError(f"Unknown primitive: {p_name}")
                        
                elif strategy == "code":
                    code = data.get("python_code")
                    if not code:
                        raise ValueError("Strategy 'code' selected but no python_code provided.")
                    # Execute code safely
                    return await asyncio.to_thread(execute_diagram_code, code)
                else:
                    raise ValueError(f"Unknown strategy: {strategy}")
                    
            except (CodeValidationError, CodeExecutionTimeout, CodeExecutionError) as e:
                if not retry_error:
                    logger.warning(f"Code execution failed, retrying: {e}")
                    return await self._generate_diagram_bytes(description, question_text, retry_error=str(e))
                else:
                    logger.error(f"Diagram generation failed after retry: {e}")
                    return _placeholder_png(f"Code execution failed: {e}")
            except Exception as e:
                logger.error(f"Diagram generation error: {e}")
                return _placeholder_png(f"Generation error: {e}")

    async def generate_diagram_and_upload(
        self,
        question_text: str,
        detection: dict,
        storage_service,
        user_id: str
    ) -> str | None:
        """
        Generates the diagram and uploads it to storage.
        """
        if not detection or not detection.get('needs_diagram'):
            return None
            
        description = detection.get('diagram_description', '')
        if not description:
            description = "Educational diagram for the following question."
            
        try:
            png_bytes = await self._generate_diagram_bytes(description, question_text)
            if not png_bytes:
                return None
                
            filename = f"diagrams/{user_id}/{uuid4()}.png"
            url = await asyncio.to_thread(
                storage_service.upload_file,
                bucket=settings.MINIO_BUCKET_USER,
                key=filename,
                file_bytes=png_bytes,
                content_type="image/png"
            )
            return url
        except Exception as e:
            logger.error(f"Failed to generate and upload diagram: {e}")
            return None

diagram_service = DiagramGenerationService()
