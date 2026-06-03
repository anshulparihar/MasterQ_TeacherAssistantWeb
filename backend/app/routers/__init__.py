from fastapi import APIRouter

from .auth import router as auth_router
from .documents import router as documents_router
from .questions import router as questions_router
from .chatbot import router as chatbot_router
from .topics import router as topics_router
from .subjects import router as subjects_router
from .exam_types import router as exam_types_router
from .admin import router as admin_router
from .export import router as export_router

api_router = APIRouter()

api_router.include_router(auth_router)
api_router.include_router(documents_router)
api_router.include_router(questions_router)
api_router.include_router(chatbot_router)
api_router.include_router(topics_router)
api_router.include_router(subjects_router)
api_router.include_router(exam_types_router)
api_router.include_router(admin_router)
api_router.include_router(export_router)
