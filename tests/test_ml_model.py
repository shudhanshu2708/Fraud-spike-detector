from app.services.ml_model import fraud_model


def test_fraud_model_prediction():
    fraud_model.load()

    probability = fraud_model.predict_probability(
        amount=18000,
        transactions_1m=10,
        transactions_5m=20,
        amount_5m=60000,
        new_device=True,
        new_ip=True,
    )

    assert 0.0 <= probability <= 1.0

    print(f"Fraud probability: {probability}")


def test_risk_decisions():
    assert fraud_model.decide(0.10) == "SAFE"
    assert fraud_model.decide(0.30) == "REVIEW"
    assert fraud_model.decide(0.50) == "REVIEW"
    assert fraud_model.decide(0.69) == "REVIEW"
    assert fraud_model.decide(0.70) == "BLOCK"
    assert fraud_model.decide(0.95) == "BLOCK"