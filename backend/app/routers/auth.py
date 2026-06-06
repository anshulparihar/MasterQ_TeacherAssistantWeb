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
    """
    Register a new user (teacher) in the MasterQ platform.

    - **user_in**: Schema containing the email, password, and full name.
    - **db**: Asynchronous database session dependency.

    Returns the generated JWT access token upon successful registration.
    """
    # Check if a user with the provided email address already exists in the database.
    user = await get_user_by_email(db, email=user_in.email)
    if user:
        # Log the warning and raise HTTP 400 Bad Request to prevent duplicate registration.
        logger.warning("registration_failed_email_exists", email=user_in.email)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )
    # Call the service layer to hash the password and insert the new user record.
    user = await register_user(db, user_in)
    # Log successful registration with the newly created user's ID.
    logger.info("user_registered", user_id=str(user.id), email=user.email)
    # Generate the JWT access token using the user's primary key (subject).
    access_token = create_access_token(subject=user.id)
    # Return the generated bearer token to the client.
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: AsyncSession = Depends(get_db)
):
    """
    Authenticate a user using their email (username) and password.

    - **form_data**: Standard OAuth2 password request form (username/password).
    - **db**: Asynchronous database session dependency.

    Returns a JWT access token if authentication is successful.
    """
    # Call the service layer to query the database and verify the password.
    user = await authenticate_user(db, email=form_data.username, password=form_data.password)
    if not user:
        # If authentication fails, log and raise HTTP 401 Unauthorized.
        logger.warning("login_failed_incorrect_credentials", email=form_data.username)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    # If the user exists but has been marked inactive, block access.
    elif not user.is_active:
        logger.warning("login_failed_inactive_user", email=form_data.username)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
        
    # Log successful login auditing the action.
    logger.info("user_logged_in", user_id=str(user.id), email=user.email)
    # Generate the JWT access token specifying the user ID as subject.
    access_token = create_access_token(subject=user.id)
    # Return the bearer token back to the authenticated client.
    return {"access_token": access_token, "token_type": "bearer"}

@router.get("/me", response_model=UserResponse)
async def read_current_user(
    current_user: User = Depends(get_current_user)
):
    """
    Retrieve the current logged-in user's profile details.

    - **current_user**: Automatically injected user instance extracted from the Bearer token.
    """
    # Directly return the user model populated by the current user dependency.
    return current_user

@router.put("/me", response_model=UserResponse)
async def update_current_user(
    full_name: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update the authenticated user's full name.

    - **full_name**: The new full name to apply to the user profile.
    - **current_user**: Injected current logged-in user instance.
    - **db**: Asynchronous database session dependency.
    """
    # Update the full name attribute on the current user instance.
    current_user.full_name = full_name
    # Commit the changes asynchronously to save them in PostgreSQL.
    await db.commit()
    # Refresh the object state to ensure it matches the database.
    await db.refresh(current_user)
    # Return the updated user database model.
    return current_user
