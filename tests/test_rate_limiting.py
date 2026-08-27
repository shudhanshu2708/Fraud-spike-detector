import pytest
from fastapi import HTTPException

from app.services.rate_limiting import check_rate_limit


class FakeClient:
    host = "127.0.0.1"


class FakeRequest:
    client = FakeClient()


def test_rate_limit_blocks_after_limit():
    request = FakeRequest()

    for _ in range(5):
        check_rate_limit(
            request=request,
            limit=5,
            window_seconds=60,
            key_suffix="test-block",
        )

    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit(
            request=request,
            limit=5,
            window_seconds=60,
            key_suffix="test-block",
        )

    assert exc_info.value.status_code == 429
    assert exc_info.value.detail == "Too many requests"
    assert "Retry-After" in exc_info.value.headers


def test_rate_limit_allows_requests_below_limit():
    request = FakeRequest()

    for _ in range(5):
        check_rate_limit(
            request=request,
            limit=5,
            window_seconds=60,
            key_suffix="test-below-limit",
        )


def test_rate_limit_keys_are_separated():
    request = FakeRequest()

    for _ in range(5):
        check_rate_limit(
            request=request,
            limit=5,
            window_seconds=60,
            key_suffix="endpoint-a",
        )

    check_rate_limit(
        request=request,
        limit=5,
        window_seconds=60,
        key_suffix="endpoint-b",
    )