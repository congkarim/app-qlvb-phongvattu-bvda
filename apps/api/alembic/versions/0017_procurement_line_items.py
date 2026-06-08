"""add procurement line items

Revision ID: 0017_procurement_line_items
Revises: 0016_document_relations
Create Date: 2026-06-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0017_procurement_line_items"
down_revision: str | None = "0016_document_relations"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "procurement_line_items",
        sa.Column("procurement_id", uuid_type, nullable=False),
        sa.Column("line_number", sa.Integer(), nullable=False),
        sa.Column("item_name", sa.String(length=512), nullable=False),
        sa.Column("item_code", sa.String(length=64), nullable=True),
        sa.Column("unit", sa.String(length=32), nullable=True),
        sa.Column("quantity", sa.Numeric(18, 4), nullable=False, server_default="1"),
        sa.Column("unit_price", sa.Numeric(18, 2), nullable=True),
        sa.Column("amount", sa.Numeric(18, 2), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["procurement_id"], ["procurement_records.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("procurement_line_items", "quantity", server_default=None)
    op.create_index(
        "ux_procurement_line_items_procurement_line_active",
        "procurement_line_items",
        ["procurement_id", "line_number"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_procurement_line_items_procurement_active",
        "procurement_line_items",
        ["procurement_id", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_line_items_item_name_active",
        "procurement_line_items",
        ["item_name", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_line_items_item_code_active",
        "procurement_line_items",
        ["item_code", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_procurement_line_items_item_code_active", table_name="procurement_line_items")
    op.drop_index("ix_procurement_line_items_item_name_active", table_name="procurement_line_items")
    op.drop_index("ix_procurement_line_items_procurement_active", table_name="procurement_line_items")
    op.drop_index(
        "ux_procurement_line_items_procurement_line_active",
        table_name="procurement_line_items",
    )
    op.drop_table("procurement_line_items")
