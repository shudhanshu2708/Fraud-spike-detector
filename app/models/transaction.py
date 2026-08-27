from sqlalchemy import (
    JSON,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.sql import func

from app.database import Base


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    amount = Column(
        Numeric(12, 2),
        nullable=False,
    )

    currency = Column(
        String(3),
        nullable=False,
        default="INR",
    )

    merchant_id = Column(
        String(100),
        nullable=False,
        index=True,
    )

    device_id = Column(
        String(255),
        nullable=False,
        index=True,
    )

    ip_address = Column(
        String(45),
        nullable=False,
        index=True,
    )

    idempotency_key = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="APPROVED",
        index=True,
    )

    risk_score = Column(
        Float,
        nullable=True,
    )

    risk_decision = Column(
        String(20),
        nullable=True,
        index=True,
    )

    risk_reasons = Column(
        JSON,
        nullable=True,
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )