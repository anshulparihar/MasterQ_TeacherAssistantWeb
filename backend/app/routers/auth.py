from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Annotated

from app.database import get_db
from app.schemas.user import UserCreate, UserResponse, Token
from app.core.security import create_access_token
from app.core.deps import get_current_user
from app.models.user import User
from app.services.auth_service import register_user, authenticate_user, get_user_by_email
import structlog

logger = structlog.get_logger(__name__)

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=Token, status_code=status.HTTP_201_CREATED)
async def register(
    user_in: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        logger.warning("registration_failed_email_exists", email=user_in.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    user = await register_user(db, user_in)
    logger.info("user_registered", user_id=str(user.id), email=user.email)
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        logger.warning("login_failed_incorrect_credentials", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user.is_active:
        logger.warning("login_failed_inactive_user", email=form_data.username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        
    logger.info("user_logged_in", user_id=str(user.id), email=user.email)
    access_token = create_access_token(subject=user.id)
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    current_user.full_name = full_name
    await db.commit()
    await db.refresh(current_user)
    return current_user
