"""add dispatch records

Revision ID: 0013_dispatch_records
Revises: 0012_admin_catalogs
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0013_dispatch_records"
down_revision: str | None = "0012_admin_catalogs"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "dispatch_records",
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("dispatch_type", sa.String(length=16), nullable=False),
        sa.Column("document_number", sa.String(length=128), nullable=True),
        sa.Column("document_symbol", sa.String(length=128), nullable=True),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("issuing_agency", sa.String(length=255), nullable=True),
        sa.Column("recipient", sa.Text(), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("dispatch_records", "status", server_default=None)
    op.create_index(
        "ux_dispatch_records_document_active",
        "dispatch_records",
        ["document_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_dispatch_records_dispatch_type_active",
        "dispatch_records",
        ["dispatch_type", "deleted_at"],
    )
    op.create_index(
        "ix_dispatch_records_document_number_active",
        "dispatch_records",
        ["document_number", "deleted_at"],
    )
    op.create_index(
        "ix_dispatch_records_issuing_agency_active",
        "dispatch_records",
        ["issuing_agency", "deleted_at"],
    )
    op.create_index(
        "ix_dispatch_records_issued_date_active",
        "dispatch_records",
        ["issued_date", "deleted_at"],
    )
    op.create_index(
        "ix_dispatch_records_status_active",
        "dispatch_records",
        ["status", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_dispatch_records_status_active", table_name="dispatch_records")
    op.drop_index("ix_dispatch_records_issued_date_active", table_name="dispatch_records")
    op.drop_index("ix_dispatch_records_issuing_agency_active", table_name="dispatch_records")
    op.drop_index("ix_dispatch_records_document_number_active", table_name="dispatch_records")
    op.drop_index("ix_dispatch_records_dispatch_type_active", table_name="dispatch_records")
    op.drop_index("ux_dispatch_records_document_active", table_name="dispatch_records")
    op.drop_table("dispatch_records")
