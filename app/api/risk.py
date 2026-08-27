from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.services.risk_engine import calculate_risk
from app.services.velocity import get_velocity

router = APIRouter()


class RiskRequest(BaseModel):
    user_id: int
    amount: float = Field(gt=0)
    new_device: bool = False
    new_ip: bool = False


class RiskResponse(BaseModel):
    risk_score: float
    decision: str
    reasons: list[str]
    transactions_1m: int
    transactions_5m: int
    amount_5m: float


@router.post("/score", response_model=RiskResponse)
def score_transaction(request: RiskRequest):
    velocity = get_velocity(request.user_id)

    result = calculate_risk(
        amount=request.amount,
        transaction_count_1m=velocity.transactions_1m,
        transaction_count_5m=velocity.transactions_5m,
        new_device=request.new_device,
        new_ip=request.new_ip,
    )

    return RiskResponse(
        risk_score=result.score,
        decision=result.decision,
        reasons=result.reasons,
        transactions_1m=velocity.transactions_1m,
        transactions_5m=velocity.transactions_5m,
        amount_5m=velocity.amount_5m,
    )