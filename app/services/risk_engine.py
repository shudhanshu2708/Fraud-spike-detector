from dataclasses import dataclass

from app.services.ml_model import fraud_model


@dataclass
class RiskResult:
    score: float
    decision: str
    reasons: list[str]


def calculate_risk(
    amount: float,
    transaction_count_1m: int,
    transaction_count_5m: int,
    amount_5m: float,
    new_device: bool,
    new_ip: bool,
) -> RiskResult:
    """
    Calculate fraud risk using the trained ML model.

    The ML model produces the primary risk score.
    Rule-based signals are retained as human-readable
    explanations for the decision.
    """
    score = fraud_model.predict_probability(
        amount=amount,
        transactions_1m=transaction_count_1m,
        transactions_5m=transaction_count_5m,
        amount_5m=amount_5m,
        new_device=new_device,
        new_ip=new_ip,
    )

    reasons: list[str] = []

    if transaction_count_1m >= 5:
        reasons.append("high_transaction_velocity_1m")
    elif transaction_count_1m >= 3:
        reasons.append("elevated_transaction_velocity_1m")

    if transaction_count_5m >= 10:
        reasons.append("high_transaction_velocity_5m")

    if amount_5m >= 5000:
        reasons.append("high_amount_velocity_5m")

    if amount >= 5000:
        reasons.append("high_transaction_amount")

    if new_device:
        reasons.append("new_device")

    if new_ip:
        reasons.append("new_ip")

    decision = fraud_model.decide(score)

    if decision == "SAFE":
        reasons = ["low_fraud_risk"]

    return RiskResult(
        score=score,
        decision=decision,
        reasons=reasons,
    )