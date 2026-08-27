from app.auth.security import (
    create_refresh_token,
    store_refresh_token,
)

def test_get_current_user(client):
    response = client.get("/auth/me")

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == 8
    assert data["email"] == "test-user@vendlyexample.com"
    assert data["role"] == "customer"

def test_me_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/auth/me")

    assert response.status_code == 401

def test_logout_revokes_refresh_token(client):
    email = "test-user@vendlyexample.com"
    refresh_token = create_refresh_token()

    store_refresh_token(
        email,
        refresh_token,
    )

    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 200
    assert response.json()["logout"] == "ok"

    # Token should no longer be usable
    response = client.post(
        "/auth/refresh",
        json={
            "refresh_token": refresh_token,
        },
    )

    assert response.status_code == 401


def test_logout_invalid_refresh_token(client):
    response = client.post(
        "/auth/logout",
        json={
            "refresh_token": "invalid-token",
        },
    )

    assert response.status_code == 401


def test_logout_all_revokes_all_sessions(client):
    email = "test-user@vendlyexample.com"

    token_1 = create_refresh_token()
    token_2 = create_refresh_token()

    store_refresh_token(email, token_1)
    store_refresh_token(email, token_2)

    response = client.post("/auth/logout-all")

    assert response.status_code == 200

    data = response.json()

    assert data["logout_all"] == "ok"
    assert data["sessions_revoked"] == 2

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": token_1},
    )

    assert response.status_code == 401

    response = client.post(
        "/auth/refresh",
        json={"refresh_token": token_2},
    )

    assert response.status_code == 401


def test_change_password_success(client):
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "test-password",
            "new_password": "new-test-password",
        },
    )

    assert response.status_code == 200
    assert (
        response.json()["message"]
        == "Password changed successfully"
    )


def test_change_password_rejects_old_password(client):
    response = client.post(
        "/auth/change-password",
        json={
            "current_password": "test-password",
            "new_password": "new-test-password",
        },
    )

    assert response.status_code == 200

    login_response = client.post(
        "/auth/login",
        json={
            "email": "test-user@vendlyexample.com",
            "password": "test-password",
        },
    )

    assert login_response.status_code == 401

