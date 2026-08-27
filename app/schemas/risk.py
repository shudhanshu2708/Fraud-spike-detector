from datetime import datetime

from pydantic import BaseModel


class FeatureCacheStatus(BaseModel):
    velocity_updated: bool
    identity_updated: bool


class TransactionRiskResponse(BaseModel):
    transaction_id: int | None = None
    transaction_created: bool
    status: str | None = None

    risk_score: float
    decision: str
    reasons: list[str]

    transactions_1m: int
    transactions_5m: int
    amount_5m: float

    created_at: datetime | None = None

    feature_cache: FeatureCacheStatus | None = None