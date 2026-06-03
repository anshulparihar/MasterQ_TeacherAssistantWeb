import asyncio
import time
import structlog
from contextlib import asynccontextmanager
from app.config import settings

logger = structlog.get_logger()

class GlobalSemaphores:
    _llm_semaphore = None
    _embedding_semaphore = None

    @classmethod
    def get_llm_semaphore(cls) -> asyncio.Semaphore:
        if cls._llm_semaphore is None:
            cls._llm_semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)
        return cls._llm_semaphore

    @classmethod
    def get_embedding_semaphore(cls) -> asyncio.Semaphore:
        if cls._embedding_semaphore is None:
            cls._embedding_semaphore = asyncio.Semaphore(settings.EMBEDDING_SEMAPHORE_LIMIT)
        return cls._embedding_semaphore

@asynccontextmanager
async def acquire_llm_semaphore(timeout: float = 60.0):
    sem = GlobalSemaphores.get_llm_semaphore()
    start_time = time.time()
    try:
        # Wait for semaphore with timeout
        await asyncio.wait_for(sem.acquire(), timeout=timeout)
        wait_time = time.time() - start_time
        if wait_time > 2.0:
            logger.warning("LLM Semaphore acquisition delayed", wait_time_seconds=round(wait_time, 2))
        yield
    except asyncio.TimeoutError:
        logger.error("LLM Semaphore acquisition timed out", timeout=timeout)
        raise RuntimeError("LLM request queue is full. Please try again later.")
    finally:
        sem.release()

@asynccontextmanager
async def acquire_embedding_semaphore(timeout: float = 30.0):
    sem = GlobalSemaphores.get_embedding_semaphore()
    start_time = time.time()
    try:
        await asyncio.wait_for(sem.acquire(), timeout=timeout)
        wait_time = time.time() - start_time
        if wait_time > 2.0:
            logger.warning("Embedding Semaphore acquisition delayed", wait_time_seconds=round(wait_time, 2))
        yield
    except asyncio.TimeoutError:
        logger.error("Embedding Semaphore acquisition timed out", timeout=timeout)
        raise RuntimeError("Embedding service is currently overloaded.")
    finally:
        sem.release()
