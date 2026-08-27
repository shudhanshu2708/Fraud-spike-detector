from dataclasses import dataclass
from time import time
from uuid import uuid4

from app.redis_client import redis_client

class VelocityStoreUnavailable(Exception):
    """Raised when the Redis velocity store is unavailable."""
    


@dataclass
class VelocityFeatures:
    transactions_1m: int
    transactions_5m: int
    amount_5m: float


def _get_key(user_id: int) -> str:
    return f"user:{user_id}:velocity"


def record_transaction(
    user_id: int,
    amount: float,
) -> bool:
    """
    Record transaction velocity in Redis.

    Redis is a derived feature store, so a Redis failure
    must not invalidate an already-persisted transaction.

    Returns:
        True  -> Redis update succeeded
        False -> Redis update failed
    """
    try:
        now = time()
        key = _get_key(user_id)

        transaction_id = str(uuid4())

        # Store transaction timestamp.
        redis_client.zadd(
            key,
            {transaction_id: now},
        )

        # Store transaction amount separately.
        redis_client.hset(
            f"{key}:amounts",
            transaction_id,
            float(amount),
        )

        # Keep only the last 5 minutes.
        cutoff = now - 300

        redis_client.zremrangebyscore(
            key,
            0,
            cutoff,
        )

        # Remove stale amount entries.
        active_ids = redis_client.zrange(
            key,
            0,
            -1,
        )

        amount_key = f"{key}:amounts"

        all_amount_ids = redis_client.hkeys(
            amount_key
        )

        stale_ids = set(all_amount_ids) - set(active_ids)

        if stale_ids:
            redis_client.hdel(
                amount_key,
                *stale_ids,
            )

        return True

    except Exception:
        return False


def get_velocity(
    user_id: int,
) -> VelocityFeatures:
    try:
        now = time()
        key = _get_key(user_id)

        cutoff_5m = now - 300
        cutoff_1m = now - 60

        transactions = redis_client.zrange(
            key,
            0,
            -1,
            withscores=True,
        )

        transactions_1m = 0
        transactions_5m = 0
        amount_5m = 0.0

        amount_key = f"{key}:amounts"

        for transaction_id, timestamp in transactions:
            if timestamp < cutoff_5m:
                continue

            transactions_5m += 1

            amount = redis_client.hget(
                amount_key,
                transaction_id,
            )

            if amount is not None:
                amount_5m += float(amount)

            if timestamp >= cutoff_1m:
                transactions_1m += 1

        return VelocityFeatures(
            transactions_1m=transactions_1m,
            transactions_5m=transactions_5m,
            amount_5m=round(amount_5m, 2),
        )

    except Exception as exc:
        raise VelocityStoreUnavailable(
            "Redis velocity store is unavailable"
        ) from exc