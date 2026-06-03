import asyncio
import google.generativeai as genai
from tenacity import retry, wait_exponential, stop_after_attempt, retry_if_exception_type
from app.config import settings
import structlog

logger = structlog.get_logger()

# Configure the Gemini SDK
genai.configure(api_key=settings.GEMINI_API_KEY)

class EmbeddingService:
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.EMBEDDING_SEMAPHORE_LIMIT)
        self.model_name = settings.EMBEDDING_MODEL_NAME

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True
    )
    async def _embed_batch(self, texts: list[str]) -> list[list[float]]:
        async with self.semaphore:
            # We use embed_content from genai
            response = genai.embed_content(
                model=self.model_name,
                content=texts,
                task_type="retrieval_document",
                output_dimensionality=768
            )
            return response['embedding']

    async def embed_texts(self, texts: list[str]) -> list[list[float]]:
        batch_size = settings.EMBEDDING_BATCH_SIZE
        all_embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            try:
                embeddings = await self._embed_batch(batch)
                if isinstance(embeddings[0], float):
                    # API returns 1D list if only 1 string was passed
                    embeddings = [embeddings]
                all_embeddings.extend(embeddings)
            except Exception as e:
                logger.error("Failed to generate embeddings for batch", error=str(e))
                raise
                
        return all_embeddings

    async def embed_query(self, text: str) -> list[float]:
        async with self.semaphore:
            response = genai.embed_content(
                model=self.model_name,
                content=text,
                task_type="retrieval_query",
                output_dimensionality=768
            )
            return response['embedding']

embedding_service = EmbeddingService()
