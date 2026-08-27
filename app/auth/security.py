import secrets
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import jwt

from app.config import settings
from app.redis_client import redis_client


def create_refresh_token() -> str:
    return secrets.token_urlsafe(32)


def hash_password(password: str) -> str:
    hashed = bcrypt.hashpw(
        password.encode("utf-8"),
        bcrypt.gensalt(),
    )
    return hashed.decode("utf-8")


def verify_password(
    plain_password: str,
    hashed_password: str,
) -> bool:
    return bcrypt.checkpw(
        plain_password.encode("utf-8"),
        hashed_password.encode("utf-8"),
    )


def create_access_token(data: dict) -> str:
    payload = data.copy()
    payload["exp"] = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )

    return jwt.encode(
        payload,
        settings.jwt_secret_key,
        algorithm=settings.jwt_algorithm,
    )


def _decode_redis_value(value: str | bytes) -> str:
    if isinstance(value, bytes):
        return value.decode("utf-8")

    return value


def store_refresh_token(
    email: str,
    refresh_token: str,
) -> None:
    expiry_seconds = (
        settings.refresh_token_expire_days * 24 * 60 * 60
    )

    redis_client.set(
        f"refresh_token:{refresh_token}",
        email,
        ex=expiry_seconds,
    )

    redis_client.sadd(
        f"user_refresh_tokens:{email}",
        refresh_token,
    )


def revoke_refresh_token(
    refresh_token: str,
) -> str | None:
    key = f"refresh_token:{refresh_token}"
    email = redis_client.get(key)

    if not email:
        return None

    email = _decode_redis_value(email)

    redis_client.delete(key)
    redis_client.srem(
        f"user_refresh_tokens:{email}",
        refresh_token,
    )

    return email


def revoke_all_refresh_tokens(
    email: str,
) -> int:
    user_key = f"user_refresh_tokens:{email}"
    tokens = redis_client.smembers(user_key)

    if not tokens:
        return 0

    deleted = 0

    for token in tokens:
        token = _decode_redis_value(token)
        token_key = f"refresh_token:{token}"

        if redis_client.delete(token_key):
            deleted += 1

    redis_client.delete(user_key)

    return deleted