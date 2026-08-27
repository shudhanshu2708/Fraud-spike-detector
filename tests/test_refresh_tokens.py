from app.auth.security import (
    create_refresh_token,
    store_refresh_token,
    revoke_refresh_token,
    revoke_all_refresh_tokens,
)
import app.auth.security as security_module


def test_refresh_token_storage():
    email = "test-user@vendlyexample.com"
    token = create_refresh_token()

    store_refresh_token(email, token)

    stored_email = security_module.redis_client.get(
    f"refresh_token:{token}"
)

    if isinstance(stored_email, bytes):
        stored_email = stored_email.decode("utf-8")

    assert stored_email == email


def test_revoke_refresh_token():
    email = "test-user@vendlyexample.com"
    token = create_refresh_token()

    store_refresh_token(email, token)

    assert revoke_refresh_token(token) == email

    assert (
        security_module.redis_client.get(
            f"refresh_token:{token}"
        )
        is None
    )


def test_revoke_all_refresh_tokens():
    email = "test-user@vendlyexample.com"

    token_1 = create_refresh_token()
    token_2 = create_refresh_token()
    token_3 = create_refresh_token()

    store_refresh_token(email, token_1)
    store_refresh_token(email, token_2)
    store_refresh_token(email, token_3)

    revoked = revoke_all_refresh_tokens(email)

    assert revoked == 3

    assert security_module.redis_client.get(
        f"refresh_token:{token_1}"
) is None

    assert security_module.redis_client.get(
        f"refresh_token:{token_2}"
) is None

    assert security_module.redis_client.get(
        f"refresh_token:{token_3}"
) is None