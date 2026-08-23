from jose import jwt
from datetime import datetime, timedelta
from app.config import settings
import secrets
import bcrypt
from app.redis_client import redis_client


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)

def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt())
    return hashed.decode("utf-8")
def verify_password(plain_password: str , hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode("utf-8"), hashed_password.encode("utf-8"))

def create_access_token(data: dict) ->str:
    to_encode = data.copy()
    to_encode["exp"] = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)
    return jwt.encode(to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm)

def store_refresh_token(email : str , refresh_token : str):
    expiry_seconds = settings.refresh_token_expire_days * 24 * 60 * 60
    redis_client.setex(f"refresh_token:{refresh_token}", expiry_seconds, email)