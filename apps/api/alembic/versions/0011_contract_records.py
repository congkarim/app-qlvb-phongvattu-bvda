"""add contract records

Revision ID: 0011_contract_records
Revises: 0010_ocr_job_retry_fields
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0011_contract_records"
down_revision: str | None = "0010_ocr_job_retry_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "contract_records",
        sa.Column("document_id", uuid_type, nullable=False),
        sa.Column("contract_number", sa.String(length=128), nullable=True),
        sa.Column("contract_title", sa.String(length=512), nullable=True),
        sa.Column("supplier_name", sa.String(length=255), nullable=True),
        sa.Column("sign_date", sa.Date(), nullable=True),
        sa.Column("effective_from", sa.Date(), nullable=True),
        sa.Column("effective_to", sa.Date(), nullable=True),
        sa.Column("contract_value", sa.Numeric(18, 2), nullable=True),
        sa.Column("currency", sa.String(length=8), nullable=False, server_default="VND"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="draft"),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("contract_records", "currency", server_default=None)
    op.alter_column("contract_records", "status", server_default=None)
    op.create_index(
        "ux_contract_records_document_active",
        "contract_records",
        ["document_id"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_contract_records_contract_number_active", "contract_records", ["contract_number", "deleted_at"])
    op.create_index("ix_contract_records_supplier_active", "contract_records", ["supplier_name", "deleted_at"])
    op.create_index("ix_contract_records_status_active", "contract_records", ["status", "deleted_at"])
    op.create_index("ix_contract_records_sign_date_active", "contract_records", ["sign_date", "deleted_at"])
    op.create_index("ix_contract_records_effective_to_active", "contract_records", ["effective_to", "deleted_at"])


def downgrade() -> None:
    op.drop_index("ix_contract_records_effective_to_active", table_name="contract_records")
    op.drop_index("ix_contract_records_sign_date_active", table_name="contract_records")
    op.drop_index("ix_contract_records_status_active", table_name="contract_records")
    op.drop_index("ix_contract_records_supplier_active", table_name="contract_records")
    op.drop_index("ix_contract_records_contract_number_active", table_name="contract_records")
    op.drop_index("ux_contract_records_document_active", table_name="contract_records")
    op.drop_table("contract_records")
