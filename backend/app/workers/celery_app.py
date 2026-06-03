from celery import Celery
import os

# Configuration variables
redis_url = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/1")

celery_app = Celery(
    "qgen_worker",
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    # Route tasks explicitly to the 'documents' queue
    task_routes={
        "backend.app.workers.*": {"queue": "documents"},
    },
    # Ensure worker concurrency limits
    worker_concurrency=4,
    worker_prefetch_multiplier=1, # Fair queueing
)

# Import the real tasks to register them
import app.workers.document_worker
