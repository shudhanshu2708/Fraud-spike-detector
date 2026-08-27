import time

from fastapi import HTTPException, Request

from app.redis_client import redis_client


def check_rate_limit(
    request: Request,
    limit: int,
    window_seconds: int,
    key_suffix: str,
) -> None:
    """
    Enforce a fixed-window rate limit using Redis.

    Redis failure does not block the request.
    """

    try:
        client_ip = request.client.host if request.client else "unknown"

        window = int(time.time()) // window_seconds

        key = (
            f"rate_limit:"
            f"{key_suffix}:"
            f"{client_ip}:"
            f"{window}"
        )

        current_count = redis_client.incr(key)

        if current_count == 1:
            redis_client.expire(
                key,
                window_seconds,
            )

        if current_count > limit:
            remaining = window_seconds - (
                int(time.time()) % window_seconds
            )

            raise HTTPException(
                status_code=429,
                detail="Too many requests",
                headers={
                    "Retry-After": str(max(1, remaining)),
                },
            )

    except HTTPException:
        raise

    except Exception:
        # Rate limiting is a protection layer.
        # Redis failure must not make the API unavailable.
        return