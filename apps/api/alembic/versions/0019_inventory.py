"""add inventory stock balances and movements

Revision ID: 0019_inventory
Revises: 0018_materials_catalog
Create Date: 2026-06-10
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0019_inventory"
down_revision: str | None = "0018_materials_catalog"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.add_column(
        "materials_catalog",
        sa.Column("min_stock_level", sa.Numeric(precision=18, scale=4), nullable=True),
    )

    op.create_table(
        "stock_balances",
        sa.Column("catalog_item_id", uuid_type, nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False, server_default=sa.text("0")),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["materials_catalog.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("catalog_item_id", name="ux_stock_balances_catalog_item_id"),
    )
    op.alter_column("stock_balances", "quantity", server_default=None)

    op.create_index(
        "ix_stock_balances_catalog_item_active",
        "stock_balances",
        ["catalog_item_id", "deleted_at"],
    )

    op.create_table(
        "stock_movements",
        sa.Column("catalog_item_id", uuid_type, nullable=False),
        sa.Column("movement_type", sa.String(length=8), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("movement_date", sa.Date(), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("reference_number", sa.String(length=128), nullable=True),
        sa.Column("procurement_id", uuid_type, nullable=True),
        sa.Column("balance_after", sa.Numeric(precision=18, scale=4), nullable=False),
        sa.Column("created_by_user_id", uuid_type, nullable=False),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["catalog_item_id"], ["materials_catalog.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["procurement_id"], ["procurement_records.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("movement_type IN ('in', 'out')", name="ck_stock_movements_movement_type"),
        sa.CheckConstraint("quantity > 0", name="ck_stock_movements_quantity_positive"),
    )

    op.create_index(
        "ix_stock_movements_catalog_item_active",
        "stock_movements",
        ["catalog_item_id", "deleted_at"],
    )
    op.create_index(
        "ix_stock_movements_movement_date_active",
        "stock_movements",
        ["movement_date", "deleted_at"],
    )
    op.create_index(
        "ix_stock_movements_movement_type_active",
        "stock_movements",
        ["movement_type", "deleted_at"],
    )
    op.create_index(
        "ix_stock_movements_procurement_active",
        "stock_movements",
        ["procurement_id", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_stock_movements_procurement_active", table_name="stock_movements")
    op.drop_index("ix_stock_movements_movement_type_active", table_name="stock_movements")
    op.drop_index("ix_stock_movements_movement_date_active", table_name="stock_movements")
    op.drop_index("ix_stock_movements_catalog_item_active", table_name="stock_movements")
    op.drop_table("stock_movements")

    op.drop_index("ix_stock_balances_catalog_item_active", table_name="stock_balances")
    op.drop_table("stock_balances")

    op.drop_column("materials_catalog", "min_stock_level")
