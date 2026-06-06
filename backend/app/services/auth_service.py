import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password, verify_password

async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    """
    Retrieve a user from the database matching the provided email address.

    - **db**: The asynchronous SQLAlchemy database session.
    - **email**: The unique email address to search for.
    """
    # Execute an asynchronous SELECT query to retrieve a user model filtering by email.
    result = await db.execute(select(User).where(User.email == email))
    # Extract the first matching scalar value from the query result, returning None if not found.
    return result.scalars().first()

async def get_user_by_id(db: AsyncSession, user_id: str | uuid.UUID) -> User | None:
    """
    Retrieve a user from the database matching the provided primary key (UUID).

    - **db**: The asynchronous SQLAlchemy database session.
    - **user_id**: The unique user identifier, either as a UUID object or a string representation.
    """
    # If the user_id is provided as a string, attempt to parse it into a UUID object.
    if isinstance(user_id, str):
        try:
            # Parse the string user_id; if invalid, return None early.
            user_id = uuid.UUID(user_id)
        except ValueError:
            # Return None if the provided user ID string is not a valid UUID format.
            return None
    # Execute a query looking up the User record with the resolved UUID.
    result = await db.execute(select(User).where(User.id == user_id))
    # Fetch the first matching scalar from the query result set.
    return result.scalars().first()

async def register_user(db: AsyncSession, data: UserCreate) -> User:
    """
    Create a new user record in the database.

    - **db**: The asynchronous SQLAlchemy database session.
    - **data**: Validation schema containing email, full name, and raw password.
    """
    # Instantiate a new User database model, hashing the plaintext password using bcrypt.
    db_user = User(
        email=data.email,
        full_name=data.full_name,
        hashed_password=hash_password(data.password)
    )
    # Add the newly created user object instance to the current database transaction session.
    db.add(db_user)
    # Commit the transaction asynchronously to save the user to PostgreSQL.
    await db.commit()
    # Refresh the db_user instance to load database-generated fields (like ID and timestamps).
    await db.refresh(db_user)
    # Return the fully updated database user record.
    return db_user

async def authenticate_user(db: AsyncSession, email: str, password: str) -> User | None:
    """
    Authenticate a user by checking their email and verifying their password.

    - **db**: The asynchronous database session.
    - **email**: The user's input email.
    - **password**: The user's input plaintext password.
    """
    # Lookup the user record matching the input email address.
    user = await get_user_by_email(db, email)
    if not user:
        # Return None if the user does not exist in the database.
        return None
    # Verify the provided plaintext password against the hashed password stored in the database.
    if not verify_password(password, user.hashed_password):
        # Return None if password verification fails.
        return None
    # Authentication succeeded; return the valid user instance.
    return user
