"""create initial users and transactions tables

Revision ID: 3c574408c3e0
Revises:
Create Date: 2026-08-30 08:59:56.564448

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "3c574408c3e0"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial users and transactions tables."""

    user_role = sa.Enum(
    "customer",
    "admin",
    name="userrole",
)

    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("password_hash", sa.String(), nullable=False),
        sa.Column(
            "role",
            user_role,
            nullable=False,
            server_default="customer",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_users_id",
        "users",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_users_email",
        "users",
        ["email"],
        unique=True,
    )

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "amount",
            sa.Numeric(12, 2),
            nullable=False,
        ),
        sa.Column(
            "currency",
            sa.String(3),
            nullable=False,
            server_default="INR",
        ),
        sa.Column(
            "merchant_id",
            sa.String(100),
            nullable=False,
        ),
        sa.Column(
            "device_id",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "ip_address",
            sa.String(45),
            nullable=False,
        ),
        sa.Column(
            "idempotency_key",
            sa.String(255),
            nullable=False,
        ),
        sa.Column(
            "status",
            sa.String(20),
            nullable=False,
            server_default="APPROVED",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index(
        "ix_transactions_id",
        "transactions",
        ["id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_user_id",
        "transactions",
        ["user_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_merchant_id",
        "transactions",
        ["merchant_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_device_id",
        "transactions",
        ["device_id"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_ip_address",
        "transactions",
        ["ip_address"],
        unique=False,
    )

    op.create_index(
        "ix_transactions_idempotency_key",
        "transactions",
        ["idempotency_key"],
        unique=True,
    )

    op.create_index(
        "ix_transactions_created_at",
        "transactions",
        ["created_at"],
        unique=False,
    )


def downgrade() -> None:
    """Drop initial users and transactions tables."""

    op.drop_table("transactions")

    op.drop_index(
        "ix_users_email",
        table_name="users",
    )

    op.drop_index(
        "ix_users_id",
        table_name="users",
    )

    op.drop_table("users")

    sa.Enum(
        "customer",
        "admin",
        name="userrole",
    ).drop(op.get_bind())