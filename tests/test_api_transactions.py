from unittest.mock import patch
from app.services.velocity import VelocityStoreUnavailable
from app.models.transaction import Transaction
from app.models.user import User



def test_unauthenticated_transaction_api(unauthenticated_client):
    response = unauthenticated_client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "api-unauthenticated-001",
        },
        json={
            "amount": 500,
            "currency": "INR",
            "merchant_id": "api_test",
            "device_id": "unauthenticated-device",
            "ip_address": "10.100.100.20",
        },
    )

    assert response.status_code == 401

def test_redis_unavailable_api(client, db_session):
    with patch(
        "app.api.transactions.get_velocity",
        side_effect=VelocityStoreUnavailable(
            "Redis unavailable"
        ),
    ):
        response = client.post(
            "/transactions/",
            headers={
                "Idempotency-Key": "api-redis-down-001",
            },
            json={
                "user_id": 8,
                "amount": 500,
                "currency": "INR",
                "merchant_id": "api_test",
                "device_id": "redis-down-device",
                "ip_address": "10.100.100.30",
            },
        )

    assert response.status_code == 503
    assert (
        response.json()["detail"]
        == "Fraud feature store temporarily unavailable"
    )

def test_get_transactions_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/transactions/")

    assert response.status_code == 401

def test_get_transactions_returns_current_user_transactions(
    client,
    db_session,
):
    transaction_1 = Transaction(
        user_id=8,
        amount=500,
        currency="INR",
        merchant_id="history-merchant-1",
        device_id="history-device-1",
        ip_address="10.0.0.1",
        idempotency_key="history-test-001",
        status="APPROVED",
    )

    transaction_2 = Transaction(
        user_id=8,
        amount=1000,
        currency="INR",
        merchant_id="history-merchant-2",
        device_id="history-device-2",
        ip_address="10.0.0.2",
        idempotency_key="history-test-002",
        status="REVIEW",
    )

    db_session.add_all([
        transaction_1,
        transaction_2,
    ])
    db_session.commit()

    response = client.get("/transactions/")

    assert response.status_code == 200

    data = response.json()

    assert all(
        transaction["user_id"] == 8
        for transaction in data["items"]
)

    assert all(
        transaction["merchant_id"] != "other-user-merchant"
        for transaction in data["items"]
)

    assert len(data["items"]) == 2
    assert data["total"] == 2
    assert data["page"] == 1
    assert data["page_size"] == 20
    assert data["has_next"] is False

    assert data["items"][0]["user_id"] == 8
    assert data["items"][1]["user_id"] == 8

def test_safe_transaction_api(client, db_session):
    response = client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "api-safe-test-001",
        },
        json={
            "user_id": 8,
            "amount": 500,
            "currency": "INR",
            "merchant_id": "api_test",
            "device_id": "api-safe-device-001",
            "ip_address": "10.100.100.1",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["transaction_created"] is True
    assert data["status"] == "APPROVED"
    assert data["decision"] == "SAFE"
    assert data["transaction_id"] is not None

def test_duplicate_idempotency_key_api(client, db_session):
    payload = {
        "user_id": 8,
        "amount": 500,
        "currency": "INR",
        "merchant_id": "api_test",
        "device_id": "idempotency-device-001",
        "ip_address": "10.100.100.10",
    }

    headers = {
        "Idempotency-Key": "api-idempotency-test-001",
    }

    first_response = client.post(
        "/transactions/",
        headers=headers,
        json=payload,
    )

    assert first_response.status_code == 201

    first_data = first_response.json()

    assert first_data["transaction_created"] is True

    second_response = client.post(
        "/transactions/",
        headers=headers,
        json=payload,
    )

    assert second_response.status_code == 200

    second_data = second_response.json()

    assert second_data["transaction_created"] is False
    assert second_data["status"] == first_data["status"]
    assert second_data["decision"] == first_data["decision"]
    assert second_data["risk_score"] == first_data["risk_score"]
    assert second_data["reasons"] == first_data["reasons"]
    assert second_data["transaction_id"] == first_data["transaction_id"]
    assert second_data["created_at"] == first_data["created_at"]



def test_review_transaction_api(client, db_session, seed_velocity):
    seed_velocity(
        user_id=8,
        transactions=[
            ("seed-review-001", 500),
        ],
    )

    response = client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "api-review-test-001",
        },
        json={
            "user_id": 8,
            "amount": 500,
            "currency": "INR",
            "merchant_id": "api_test",
            "device_id": "api-review-device-001",
            "ip_address": "10.100.100.2",
        },
    )

    assert response.status_code == 201

    data = response.json()

    assert data["transaction_created"] is True
    assert data["status"] == "REVIEW"
    assert data["decision"] == "REVIEW"
    assert 0.30 <= data["risk_score"] < 0.70

def test_block_transaction_api(client, db_session, seed_velocity):
    seed_velocity(
        user_id=8,
        transactions=[
            ("seed-block-001", 1000),
            ("seed-block-002", 1000),
            ("seed-block-003", 1000),
            ("seed-block-004", 1000),
            ("seed-block-005", 1000),
        ],
    )

    response = client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "api-block-test-001",
        },
        json={
            "user_id": 8,
            "amount": 3000,
            "currency": "INR",
            "merchant_id": "api_test",
            "device_id": "api-block-device-001",
            "ip_address": "10.100.100.3",
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_created"] is False
    assert data["transaction_id"] is None
    assert data["decision"] == "BLOCK"
    assert data["risk_score"] >= 0.70

def test_transaction_uses_authenticated_user_id(client, db_session):
    response = client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "api-ownership-test-001",
        },
        json={
            "user_id": 999999,
            "amount": 500,
            "currency": "INR",
            "merchant_id": "api_test",
            "device_id": "ownership-device-001",
            "ip_address": "10.100.100.50",
        },
    )

    assert response.status_code == 201

    data = response.json()

    transaction = (
        db_session.query(Transaction)
        .filter(Transaction.id == data["transaction_id"])
        .first()
    )

    assert transaction is not None
    assert transaction.user_id == 8

def test_get_transactions_does_not_return_other_users_transactions(
    client,
    db_session,
):
    other_user = User(
        email="other-user@vendlyexample.com",
        password_hash="unused-test-hash",
        role="customer",
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    other_transaction = Transaction(
        user_id=other_user.id,
        amount=5000,
        currency="INR",
        merchant_id="other-user-merchant",
        device_id="other-user-device",
        ip_address="10.10.10.10",
        idempotency_key="other-user-history-001",
        status="APPROVED",
    )

    db_session.add(other_transaction)
    db_session.commit()

    response = client.get("/transactions/")

    assert response.status_code == 200

    data = response.json()

    assert all(
        transaction["user_id"] == 8
        for transaction in data["items"]
    )

    assert all(
        transaction["merchant_id"] != "other-user-merchant"
        for transaction in data["items"]
    )

def test_get_transactions_pagination(
    client,
    db_session,
):
    for i in range(5):
        db_session.add(
            Transaction(
                user_id=8,
                amount=100 + i,
                currency="INR",
                merchant_id=f"pagination-{i}",
                device_id=f"pagination-device-{i}",
                ip_address=f"10.20.0.{i + 1}",
                idempotency_key=f"pagination-test-{i}",
                status="APPROVED",
            )
        )

    db_session.commit()

    response = client.get(
        "/transactions/?page=1&page_size=2"
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["items"]) == 2
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert data["total"] >= 5
    assert data["has_next"] is True

    assert all(
        item["merchant_id"].startswith("pagination-")
        for item in data["items"]
)

def test_get_transactions_pagination_validation(client):
    response = client.get(
        "/transactions/?page=0&page_size=20"
    )

    assert response.status_code == 422

    response = client.get(
        "/transactions/?page=1&page_size=101"
    )

    assert response.status_code == 422

def test_get_transaction_requires_auth(unauthenticated_client):
    response = unauthenticated_client.get("/transactions/1")

    assert response.status_code == 401

def test_get_transaction_returns_owned_transaction(
    client,
    db_session,
):
    transaction = Transaction(
        user_id=8,
        amount=750,
        currency="INR",
        merchant_id="detail-test-merchant",
        device_id="detail-test-device",
        ip_address="10.50.0.1",
        idempotency_key="detail-test-001",
        status="APPROVED",
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = client.get(
        f"/transactions/{transaction.id}"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["id"] == transaction.id
    assert data["user_id"] == 8
    assert data["amount"] == 750
    assert data["merchant_id"] == "detail-test-merchant"

def test_get_transaction_not_found(client):
    response = client.get("/transactions/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Transaction not found"

def test_get_transaction_cannot_access_other_user(
    client,
    db_session,
):
    other_user = User(
        email="transaction-owner@vendlyexample.com",
        password_hash="unused-test-hash",
        role="customer",
    )

    db_session.add(other_user)
    db_session.commit()
    db_session.refresh(other_user)

    transaction = Transaction(
        user_id=other_user.id,
        amount=900,
        currency="INR",
        merchant_id="private-merchant",
        device_id="private-device",
        ip_address="10.60.0.1",
        idempotency_key="private-transaction-001",
        status="APPROVED",
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = client.get(
        f"/transactions/{transaction.id}"
    )

    assert response.status_code == 404

def test_get_transactions_rejects_invalid_status(client):
    response = client.get(
        "/transactions/?status=BLOCK"
    )

    assert response.status_code == 422

def test_transaction_persists_risk_data(
    client,
    db_session,
):
    response = client.post(
        "/transactions/",
        headers={
            "Idempotency-Key": "risk-persistence-test-001",
        },
        json={
            "amount": 500,
            "currency": "INR",
            "merchant_id": "risk-persistence-merchant",
            "device_id": "risk-persistence-device",
            "ip_address": "10.80.0.1",
        },
    )

    assert response.status_code == 201

    data = response.json()

    transaction = (
        db_session.query(Transaction)
        .filter(
            Transaction.id == data["transaction_id"]
        )
        .first()
    )

    assert transaction is not None
    assert transaction.risk_score == data["risk_score"]
    assert transaction.risk_decision == data["decision"]
    assert transaction.risk_reasons == data["reasons"]

def test_admin_transactions_requires_auth(
    unauthenticated_client,
):
    response = unauthenticated_client.get(
        "/admin/transactions"
    )

    assert response.status_code == 401

def test_customer_cannot_access_admin_transactions(
    client,
):
    response = client.get(
        "/admin/transactions"
    )

    assert response.status_code == 403

def test_admin_can_access_all_transactions(
    admin_client,
    db_session,
):
    db_session.add(
        Transaction(
            user_id=8,
            amount=500,
            currency="INR",
            merchant_id="admin-test-merchant",
            device_id="admin-test-device",
            ip_address="10.90.0.1",
            idempotency_key="admin-test-001",
            status="APPROVED",
        )
    )

    db_session.commit()

    response = admin_client.get(
        "/admin/transactions"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total"] == 1
    assert len(data["items"]) == 1
    assert data["items"][0]["user_id"] == 8

def test_admin_can_approve_review_transaction(
    admin_client,
    db_session,
):
    transaction = Transaction(
        user_id=8,
        amount=500,
        currency="INR",
        merchant_id="review-approve-merchant",
        device_id="review-approve-device",
        ip_address="10.50.0.1",
        idempotency_key="review-approve-001",
        status="REVIEW",
        risk_score=0.45,
        risk_decision="REVIEW",
        risk_reasons=["new_device"],
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = admin_client.post(
        f"/admin/transactions/{transaction.id}/approve"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == transaction.id
    assert data["status"] == "APPROVED"

    db_session.refresh(transaction)

    assert transaction.status == "APPROVED"

def test_admin_can_reject_review_transaction(
    admin_client,
    db_session,
):
    transaction = Transaction(
        user_id=8,
        amount=500,
        currency="INR",
        merchant_id="review-reject-merchant",
        device_id="review-reject-device",
        ip_address="10.50.0.2",
        idempotency_key="review-reject-001",
        status="REVIEW",
        risk_score=0.55,
        risk_decision="REVIEW",
        risk_reasons=["new_ip"],
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = admin_client.post(
        f"/admin/transactions/{transaction.id}/reject"
    )

    assert response.status_code == 200

    data = response.json()

    assert data["transaction_id"] == transaction.id
    assert data["status"] == "REJECTED"

    db_session.refresh(transaction)

    assert transaction.status == "REJECTED"

def test_customer_cannot_approve_transaction(
    client,
    db_session,
):
    transaction = Transaction(
        user_id=8,
        amount=500,
        currency="INR",
        merchant_id="customer-approve-merchant",
        device_id="customer-approve-device",
        ip_address="10.50.0.3",
        idempotency_key="customer-approve-001",
        status="REVIEW",
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = client.post(
        f"/admin/transactions/{transaction.id}/approve"
    )

    assert response.status_code == 403

def test_unauthenticated_cannot_approve_transaction(
    unauthenticated_client,
):
    response = unauthenticated_client.post(
        "/admin/transactions/999999/approve"
    )

    assert response.status_code == 401

def test_admin_cannot_approve_non_review_transaction(
    admin_client,
    db_session,
):
    transaction = Transaction(
        user_id=8,
        amount=500,
        currency="INR",
        merchant_id="already-approved",
        device_id="already-approved-device",
        ip_address="10.50.0.4",
        idempotency_key="already-approved-001",
        status="APPROVED",
    )

    db_session.add(transaction)
    db_session.commit()
    db_session.refresh(transaction)

    response = admin_client.post(
        f"/admin/transactions/{transaction.id}/approve"
    )

    assert response.status_code == 400

def test_admin_review_action_transaction_not_found(
    admin_client,
):
    response = admin_client.post(
        "/admin/transactions/999999/approve"
    )

    assert response.status_code == 404

def test_idempotency_key_cannot_be_reused_for_different_transaction(
    client,
):
    headers = {
        "Idempotency-Key": "idempotency-reuse-test-001",
    }

    first_response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": 500,
            "currency": "INR",
            "merchant_id": "idempotency-merchant",
            "device_id": "idempotency-device",
            "ip_address": "10.200.0.1",
        },
    )

    assert first_response.status_code == 201

    second_response = client.post(
        "/transactions/",
        headers=headers,
        json={
            "amount": 1000,
            "currency": "INR",
            "merchant_id": "different-merchant",
            "device_id": "different-device",
            "ip_address": "10.200.0.2",
        },
    )

    assert second_response.status_code == 409