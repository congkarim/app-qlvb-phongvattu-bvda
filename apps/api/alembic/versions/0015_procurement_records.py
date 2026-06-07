"""add procurement records

Revision ID: 0015_procurement_records
Revises: 0014_decision_records
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0015_procurement_records"
down_revision: str | None = "0014_decision_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

PROCUREMENT_BUSINESS_TYPE_ID = "10000000-0000-0000-0000-000000000005"


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "procurement_records",
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("procurement_kind", sa.String(length=16), nullable=False),
        sa.Column("reference_number", sa.String(length=128), nullable=True),
        sa.Column("title_summary", sa.Text(), nullable=True),
        sa.Column("requesting_unit", sa.String(length=255), nullable=True),
        sa.Column("estimated_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="VND"),
        sa.Column("requested_date", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("procurement_records", "currency", server_default=None)
    op.alter_column("procurement_records", "status", server_default=None)
    op.create_index(
        "ux_procurement_records_document_active",
        "procurement_records",
        ["document_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_procurement_records_procurement_kind_active",
        "procurement_records",
        ["procurement_kind", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_records_reference_number_active",
        "procurement_records",
        ["reference_number", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_records_requesting_unit_active",
        "procurement_records",
        ["requesting_unit", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_records_status_active",
        "procurement_records",
        ["status", "deleted_at"],
    )
    op.create_index(
        "ix_procurement_records_requested_date_active",
        "procurement_records",
        ["requested_date", "deleted_at"],
    )

    _seed_procurement_business_type()


def downgrade() -> None:
    op.execute(
        f"""
        DELETE FROM admin_catalog_items
        WHERE id = '{PROCUREMENT_BUSINESS_TYPE_ID}'
          AND catalog_type = 'business_type'
          AND code = 'procurement'
        """
    )

    op.drop_index("ix_procurement_records_requested_date_active", table_name="procurement_records")
    op.drop_index("ix_procurement_records_status_active", table_name="procurement_records")
    op.drop_index("ix_procurement_records_requesting_unit_active", table_name="procurement_records")
    op.drop_index("ix_procurement_records_reference_number_active", table_name="procurement_records")
    op.drop_index("ix_procurement_records_procurement_kind_active", table_name="procurement_records")
    op.drop_index("ux_procurement_records_document_active", table_name="procurement_records")
    op.drop_table("procurement_records")


def _seed_procurement_business_type() -> None:
    op.execute(
        f"""
        INSERT INTO admin_catalog_items (
            id, catalog_type, code, label, sort_order, is_active, created_at, updated_at
        )
        SELECT
            '{PROCUREMENT_BUSINESS_TYPE_ID}',
            'business_type',
            'procurement',
            'Đề xuất / kế hoạch mua sắm',
            50,
            true,
            now(),
            now()
        WHERE NOT EXISTS (
            SELECT 1
            FROM admin_catalog_items
            WHERE catalog_type = 'business_type'
              AND code = 'procurement'
              AND deleted_at IS NULL
        )
        """
    )
