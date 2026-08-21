from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from app.config import settings
import secrets


pwd_content = CryptContext(schemes=["bcrypt"], depreacted="auto")

def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    return pwd_content.hash(password)

def verify_password(plain_password: str , hashed_password: str) -> bool:
    return pwd_content.verify(plain_password, hashed_password)

def create_access_token(data: dict) ->str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)