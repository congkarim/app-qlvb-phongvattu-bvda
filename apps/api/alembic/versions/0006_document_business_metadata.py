"""add document business metadata

Revision ID: 0006_document_business_metadata
Revises: 0005_document_files
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0006_document_business_metadata"
down_revision: str | None = "0005_document_files"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("document_number", sa.String(length=128), nullable=True))
    op.add_column("documents", sa.Column("issued_date", sa.Date(), nullable=True))
    op.add_column("documents", sa.Column("issuing_agency", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("business_type", sa.String(length=64), nullable=True))
    op.create_index("ix_documents_business_type", "documents", ["business_type"])
    op.create_index("ix_documents_issued_date", "documents", ["issued_date"])


def downgrade() -> None:
    op.drop_index("ix_documents_issued_date", table_name="documents")
    op.drop_index("ix_documents_business_type", table_name="documents")
    op.drop_column("documents", "business_type")
    op.drop_column("documents", "issuing_agency")
    op.drop_column("documents", "issued_date")
    op.drop_column("documents", "document_number")
