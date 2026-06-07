"""add decision records

Revision ID: 0014_decision_records
Revises: 0013_dispatch_records
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0014_decision_records"
down_revision: str | None = "0013_dispatch_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "decision_records",
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("decision_kind", sa.String(length=16), nullable=False),
        sa.Column("document_number", sa.String(length=128), nullable=True),
        sa.Column("document_symbol", sa.String(length=128), nullable=True),
        sa.Column("issued_date", sa.Date(), nullable=True),
        sa.Column("issuing_agency", sa.String(length=255), nullable=True),
        sa.Column("excerpt", sa.Text(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("decision_records", "status", server_default=None)
    op.create_index(
        "ux_decision_records_document_active",
        "decision_records",
        ["document_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_decision_records_decision_kind_active",
        "decision_records",
        ["decision_kind", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_document_number_active",
        "decision_records",
        ["document_number", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_issuing_agency_active",
        "decision_records",
        ["issuing_agency", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_issued_date_active",
        "decision_records",
        ["issued_date", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_effective_from_active",
        "decision_records",
        ["effective_from", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_effective_to_active",
        "decision_records",
        ["effective_to", "deleted_at"],
    )
    op.create_index(
        "ix_decision_records_status_active",
        "decision_records",
        ["status", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_decision_records_status_active", table_name="decision_records")
    op.drop_index("ix_decision_records_effective_to_active", table_name="decision_records")
    op.drop_index("ix_decision_records_effective_from_active", table_name="decision_records")
    op.drop_index("ix_decision_records_issued_date_active", table_name="decision_records")
    op.drop_index("ix_decision_records_issuing_agency_active", table_name="decision_records")
    op.drop_index("ix_decision_records_document_number_active", table_name="decision_records")
    op.drop_index("ix_decision_records_decision_kind_active", table_name="decision_records")
    op.drop_index("ux_decision_records_document_active", table_name="decision_records")
    op.drop_table("decision_records")
