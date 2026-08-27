from fastapi import (
    APIRouter,
    Depends,
    Header,
    HTTPException,
    Query,
    Request,
    status,
)
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth.dependencies import get_current_user
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.risk import TransactionRiskResponse
from app.schemas.transaction import (
    TransactionCreate,
    TransactionListResponse,
    TransactionResponse,
    TransactionStatus,
)
from app.services.identity_features import (
    IdentityStoreUnavailable,
    check_identity,
    record_identity,
)
from app.services.risk_engine import calculate_risk
from app.services.velocity import (
    VelocityStoreUnavailable,
    get_velocity,
    record_transaction,
)


router = APIRouter()


def _is_same_transaction(
    existing_transaction: Transaction,
    transaction: TransactionCreate,
) -> bool:
    return (
        float(existing_transaction.amount) == float(transaction.amount)
        and existing_transaction.currency == transaction.currency
        and existing_transaction.merchant_id == transaction.merchant_id
        and existing_transaction.device_id == transaction.device_id
        and existing_transaction.ip_address == transaction.ip_address
    )


def _idempotency_response(
    transaction: Transaction,
) -> dict:
    return {
        "transaction_id": transaction.id,
        "transaction_created": False,
        "risk_score": 0.0,
        "decision": "ALREADY_PROCESSED",
        "reasons": ["idempotency_key_already_processed"],
        "transactions_1m": 0,
        "transactions_5m": 0,
        "amount_5m": 0.0,
        "created_at": transaction.created_at,
    }


@router.post(
    "/",
    response_model=TransactionRiskResponse,
    status_code=status.HTTP_201_CREATED,
)
def create_transaction(
    request: Request,
    transaction: TransactionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    idempotency_key: str = Header(...),
):
    request_id = request.state.request_id

    # 1. Idempotency check
    existing_transaction = (
        db.query(Transaction)
        .filter(Transaction.idempotency_key == idempotency_key)
        .first()
    )

    if existing_transaction is not None:
        if not _is_same_transaction(
            existing_transaction,
            transaction,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key already used for a different transaction",
            )

        return _idempotency_response(existing_transaction)

    # 2. Read current velocity before this transaction
    try:
        velocity = get_velocity(current_user.id)
    except VelocityStoreUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fraud feature store temporarily unavailable",
        )

    # 3. Check device/IP history
    try:
        identity = check_identity(
            user_id=current_user.id,
            device_id=transaction.device_id,
            ip_address=transaction.ip_address,
        )
    except IdentityStoreUnavailable:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Fraud identity store temporarily unavailable",
        )

    # 4. Calculate risk
    risk = calculate_risk(
        amount=float(transaction.amount),
        transaction_count_1m=velocity.transactions_1m,
        transaction_count_5m=velocity.transactions_5m,
        amount_5m=velocity.amount_5m,
        new_device=identity.new_device,
        new_ip=identity.new_ip,
    )

    # 5. Block high-risk transaction
    if risk.decision == "BLOCK":
        return {
            "transaction_id": None,
            "transaction_created": False,
            "risk_score": risk.score,
            "decision": "BLOCK",
            "reasons": risk.reasons,
            "transactions_1m": velocity.transactions_1m,
            "transactions_5m": velocity.transactions_5m,
            "amount_5m": velocity.amount_5m,
            "created_at": None,
        }

    # 6. Persist allowed transaction
    new_transaction = Transaction(
        user_id=current_user.id,
        amount=transaction.amount,
        currency=transaction.currency,
        merchant_id=transaction.merchant_id,
        device_id=transaction.device_id,
        ip_address=transaction.ip_address,
        idempotency_key=idempotency_key,
        status=(
            "REVIEW"
            if risk.decision == "REVIEW"
            else "APPROVED"
        ),
        risk_score=risk.score,
        risk_decision=risk.decision,
        risk_reasons=risk.reasons,
    )

    try:
        db.add(new_transaction)
        db.commit()
        db.refresh(new_transaction)

    except IntegrityError as exc:
        db.rollback()

        if "ix_transactions_idempotency_key" not in str(exc):
            raise

        existing_transaction = (
            db.query(Transaction)
            .filter(
                Transaction.idempotency_key == idempotency_key
            )
            .first()
        )

        if existing_transaction is None:
            raise

        if not _is_same_transaction(
            existing_transaction,
            transaction,
        ):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Idempotency key already used for a different transaction",
            )

        return _idempotency_response(existing_transaction)

    # 7. Update Redis feature stores
    redis_velocity_updated = record_transaction(
        user_id=current_user.id,
        amount=new_transaction.amount,
    )

    redis_identity_updated = record_identity(
        user_id=current_user.id,
        device_id=new_transaction.device_id,
        ip_address=new_transaction.ip_address,
    )

    print(
        f"request_id={request_id} "
        f"transaction_id={new_transaction.id} "
        f"decision={risk.decision} "
        f"risk_score={risk.score}"
    )

    return {
        "transaction_id": new_transaction.id,
        "transaction_created": True,
        "status": new_transaction.status,
        "risk_score": risk.score,
        "decision": risk.decision,
        "reasons": risk.reasons,
        "transactions_1m": velocity.transactions_1m,
        "transactions_5m": velocity.transactions_5m,
        "amount_5m": velocity.amount_5m,
        "created_at": new_transaction.created_at,
        "feature_cache": {
            "velocity_updated": redis_velocity_updated,
            "identity_updated": redis_identity_updated,
        },
    }


@router.get(
    "/",
    response_model=TransactionListResponse,
)
def get_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: TransactionStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = (
        db.query(Transaction)
        .filter(Transaction.user_id == current_user.id)
    )

    if status_filter is not None:
        query = query.filter(
            Transaction.status == status_filter
        )

    total = query.count()
    offset = (page - 1) * page_size

    transactions = (
        query
        .order_by(Transaction.created_at.desc())
        .offset(offset)
        .limit(page_size)
        .all()
    )

    return {
        "items": transactions,
        "total": total,
        "page": page,
        "page_size": page_size,
        "has_next": offset + len(transactions) < total,
    }


@router.get(
    "/{transaction_id}",
    response_model=TransactionResponse,
)
def get_transaction(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    transaction = (
        db.query(Transaction)
        .filter(
            Transaction.id == transaction_id,
            Transaction.user_id == current_user.id,
        )
        .first()
    )

    if transaction is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found",
        )

    return transaction