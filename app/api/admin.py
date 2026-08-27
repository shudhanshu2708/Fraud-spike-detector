from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.auth.dependencies import require_admin
from app.database import get_db
from app.models.transaction import Transaction
from app.models.user import User
from app.schemas.transaction import (
    AdminTransactionListResponse,
    TransactionStatus,
)


router = APIRouter(
    prefix="/admin",
    tags=["admin"],
)


@router.get(
    "/transactions",
    response_model=AdminTransactionListResponse,
)
def get_all_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status_filter: TransactionStatus | None = Query(
        default=None,
        alias="status",
    ),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    query = db.query(Transaction)

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


def _update_review_transaction(
    transaction_id: int,
    new_status: str,
    db: Session,
):
    transaction = (
        db.query(Transaction)
        .filter(Transaction.id == transaction_id)
        .first()
    )

    if transaction is None:
        raise HTTPException(
            status_code=404,
            detail="Transaction not found",
        )

    if transaction.status != "REVIEW":
        raise HTTPException(
            status_code=400,
            detail="Only REVIEW transactions can be updated",
        )

    transaction.status = new_status

    db.commit()
    db.refresh(transaction)

    return {
        "transaction_id": transaction.id,
        "status": transaction.status,
    }


@router.post("/transactions/{transaction_id}/approve")
def approve_transaction(
    transaction_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _update_review_transaction(
        transaction_id,
        "APPROVED",
        db,
    )


@router.post("/transactions/{transaction_id}/reject")
def reject_transaction(
    transaction_id: int,
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    return _update_review_transaction(
        transaction_id,
        "REJECTED",
        db,
    )