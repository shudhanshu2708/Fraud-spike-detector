from dataclasses import dataclass

from app.redis_client import redis_client


class IdentityStoreUnavailable(Exception):
    """Raised when the Redis identity store is unavailable."""


@dataclass
class IdentityFeatures:
    new_device: bool
    new_ip: bool


def _devices_key(user_id: int) -> str:
    return f"user:{user_id}:devices"


def _ips_key(user_id: int) -> str:
    return f"user:{user_id}:ips"


def check_identity(
    user_id: int,
    device_id: str,
    ip_address: str,
) -> IdentityFeatures:
    """
    Check whether the device and IP have previously
    been associated with this user.
    """
    try:
        device_key = _devices_key(user_id)
        ip_key = _ips_key(user_id)

        new_device = not redis_client.sismember(
            device_key,
            device_id,
        )

        new_ip = not redis_client.sismember(
            ip_key,
            ip_address,
        )

        return IdentityFeatures(
            new_device=new_device,
            new_ip=new_ip,
        )

    except Exception as exc:
        raise IdentityStoreUnavailable(
            "Redis identity store is unavailable"
        ) from exc


def record_identity(
    user_id: int,
    device_id: str,
    ip_address: str,
) -> bool:
    """
    Remember the device and IP after a transaction
    has been successfully accepted.

    Returns:
        True if the Redis update succeeded.
        False if the Redis update failed.
    """
    try:
        redis_client.sadd(
            _devices_key(user_id),
            device_id,
        )

        redis_client.sadd(
            _ips_key(user_id),
            ip_address,
        )

        return True

    except Exception:
        return False