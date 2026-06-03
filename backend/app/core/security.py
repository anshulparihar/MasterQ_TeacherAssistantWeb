from datetime import datetime, timedelta
from typing import Any, Union
from jose import jwt
from app.config import settings
import bcrypt

def hash_password(password: str) -> str:
    # bcrypt requires bytes, so encode the password
    pwd_bytes = password.encode('utf-8')
    # Generate salt and hash
    hashed = bcrypt.hashpw(pwd_bytes, bcrypt.gensalt())
    return hashed.decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(
            plain_password.encode('utf-8'), 
            hashed_password.encode('utf-8')
        )
    except ValueError:
        return False


def create_access_token(subject: Union[str, Any]) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.JWT_EXPIRY_HOURS)
    to_encode = {"exp": expire, "sub": str(subject)}
    encoded_jwt = jwt.encode(
        to_encode, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt

def decode_access_token(token: str) -> dict | None:
    try:
        decoded_token = jwt.decode(
            token, settings.JWT_SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        return decoded_token if decoded_token.get("exp") >= datetime.utcnow().timestamp() else None
    except jwt.JWTError:
        return None
