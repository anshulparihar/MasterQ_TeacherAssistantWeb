from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = Field(default="postgresql+asyncpg://user:pass@postgres:5432/qgendb")
    
    # Redis & Celery
    REDIS_URL: str = Field(default="redis://redis:6379/0")
    CELERY_BROKER_URL: str = Field(default="redis://redis:6379/1")
    
    # LLM (Gemini)
    GEMINI_API_KEY: str = Field(default="")
    GEMINI_MODEL_NAME: str = Field(default="gemini-2.5-pro")
    EMBEDDING_MODEL_NAME: str = Field(default="models/text-embedding-004")
    
    # MinIO
    MINIO_ENDPOINT: str = Field(default="minio:9000")
    MINIO_ACCESS_KEY: str = Field(default="minioadmin")
    MINIO_SECRET_KEY: str = Field(default="minioadmin")
    MINIO_BUCKET_ADMIN: str = Field(default="admin-documents")
    MINIO_BUCKET_USER: str = Field(default="user-documents")
    
    # JWT Auth
    JWT_SECRET_KEY: str = Field(default="your_jwt_secret")
    JWT_ALGORITHM: str = Field(default="HS256")
    JWT_EXPIRY_HOURS: int = Field(default=24)
    
    # Concurrency
    LLM_SEMAPHORE_LIMIT: int = Field(default=5)
    EMBEDDING_SEMAPHORE_LIMIT: int = Field(default=10)
    
    # Retrieval and Chunking
    CHUNK_SIZE: int = Field(default=1000)
    CHUNK_OVERLAP: int = Field(default=200)
    MAX_RETRIEVAL_CHUNKS: int = Field(default=20)
    EMBEDDING_BATCH_SIZE: int = Field(default=50)

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
