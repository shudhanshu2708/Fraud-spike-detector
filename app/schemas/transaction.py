from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


TransactionStatus = Literal[
    "APPROVED",
    "REVIEW",
    "REJECTED",
]


class TransactionCreate(BaseModel):
    amount: float = Field(gt=0)
    currency: str = Field(
        default="INR",
        min_length=3,
        max_length=3,
    )
    merchant_id: str = Field(
        min_length=1,
        max_length=100,
    )
    device_id: str = Field(
        min_length=1,
        max_length=255,
    )
    ip_address: str = Field(
        min_length=1,
        max_length=45,
    )


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    amount: float
    currency: str
    merchant_id: str
    device_id: str
    ip_address: str
    status: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TransactionListResponse(BaseModel):
    items: list[TransactionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool


class AdminTransactionResponse(TransactionResponse):
    risk_score: float | None = None
    risk_decision: str | None = None
    risk_reasons: list[str] | None = None

    reviewed_by: int | None = None
    reviewed_at: datetime | None = None


class AdminTransactionListResponse(BaseModel):
    items: list[AdminTransactionResponse]
    total: int
    page: int
    page_size: int
    has_next: bool