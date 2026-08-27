from sqlalchemy import inspect

from app.database import engine
from app.models.transaction import Transaction


def test_idempotency_key_is_unique():
    inspector = inspect(engine)

    indexes = inspector.get_indexes("transactions")

    unique_indexes = {
        index["name"]
        for index in indexes
        if index.get("unique")
    }

    assert (
        "ix_transactions_idempotency_key"
        in unique_indexes
    )