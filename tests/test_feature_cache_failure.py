from unittest.mock import patch

from app.services.velocity import record_transaction
from app.services.identity_features import record_identity


def test_velocity_failure_returns_false():
    with patch(
        "app.services.velocity.redis_client.zadd",
        side_effect=Exception("Redis unavailable"),
    ):
        result = record_transaction(
            user_id=8,
            amount=500,
        )

    assert result is False


def test_identity_failure_returns_false():
    with patch(
        "app.services.identity_features.redis_client.sadd",
        side_effect=Exception("Redis unavailable"),
    ):
        result = record_identity(
            user_id=8,
            device_id="test-device",
            ip_address="10.0.0.1",
        )

    assert result is False