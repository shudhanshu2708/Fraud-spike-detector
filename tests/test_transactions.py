from app.services.ml_model import fraud_model
from app.services.risk_engine import calculate_risk


def setup_module():
    fraud_model.load()


def test_safe_transaction():
    risk = calculate_risk(
        amount=500,
        transaction_count_1m=0,
        transaction_count_5m=0,
        amount_5m=0,
        new_device=False,
        new_ip=False,
    )

    assert risk.decision == "SAFE"
    assert 0.0 <= risk.score < 0.30


def test_review_transaction():
    risk = calculate_risk(
        amount=500,
        transaction_count_1m=1,
        transaction_count_5m=1,
        amount_5m=500,
        new_device=True,
        new_ip=True,
    )

    assert risk.decision == "REVIEW"
    assert 0.30 <= risk.score < 0.70


def test_block_transaction():
    risk = calculate_risk(
        amount=10000,
        transaction_count_1m=5,
        transaction_count_5m=10,
        amount_5m=50000,
        new_device=True,
        new_ip=True,
    )

    assert risk.decision == "BLOCK"
    assert risk.score >= 0.70