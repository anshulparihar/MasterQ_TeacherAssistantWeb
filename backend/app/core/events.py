import logging
import asyncio
from typing import Callable
from fastapi import FastAPI

logger = logging.getLogger(__name__)

def create_start_app_handler(app: FastAPI) -> Callable:
    async def start_app() -> None:
        logger.info("Initializing MasterQ platform...")
        
        # 1. Run Alembic Migrations
        try:
            from alembic.config import Config
            from alembic import command
            import asyncio
            
            def run_upgrade():
                alembic_cfg = Config("alembic.ini")
                command.upgrade(alembic_cfg, "head")

            loop = asyncio.get_running_loop()
            await loop.run_in_executor(None, run_upgrade)
            logger.info("Database migrations applied successfully.")
        except Exception as e:
            logger.error(f"Failed to apply database migrations: {e}")
        
        # 2. Check MinIO
        try:
            from app.services.storage_service import storage_service
            # This triggers bucket creation
            storage_service._ensure_buckets()
            logger.info("MinIO connection verified and buckets ensured.")
        except Exception as e:
            logger.error(f"MinIO initialization failed: {e}")

        # 3. Check Redis connectivity (via celery or direct ping)
        try:
            from app.workers.celery_app import celery_app
            with celery_app.connection() as connection:
                connection.connect()
            logger.info("Redis/Celery broker connection verified.")
        except Exception as e:
            logger.error(f"Redis connection failed: {e}")
            
    return start_app

def create_stop_app_handler(app: FastAPI) -> Callable:
    async def stop_app() -> None:
        logger.info("Shutting down MasterQ platform...")
        # Note: sqlalchemy async engines are cleaned up implicitly in modern fastapi/sqlalchemy when the event loop closes
    return stop_app
