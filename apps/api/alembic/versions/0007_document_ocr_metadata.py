"""add OCR extracted document metadata

Revision ID: 0007_document_ocr_metadata
Revises: 0006_document_business_metadata
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0007_document_ocr_metadata"
down_revision: str | None = "0006_document_business_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("documents", sa.Column("classification_confidence", sa.Float(), nullable=True))
    op.add_column("documents", sa.Column("document_symbol", sa.String(length=128), nullable=True))
    op.add_column("documents", sa.Column("issued_place", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("excerpt", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("recipient", sa.Text(), nullable=True))
    op.add_column("documents", sa.Column("signer_name", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("signer_title", sa.String(length=255), nullable=True))
    op.add_column("documents", sa.Column("seals_present", sa.Boolean(), nullable=True))
    op.add_column("documents", sa.Column("attachment_present", sa.Boolean(), nullable=True))
    op.add_column("documents", sa.Column("page_count", sa.Integer(), nullable=True))
    op.add_column("documents", sa.Column("metadata_source", sa.String(length=32), nullable=True))
    op.add_column("documents", sa.Column("metadata_reviewed_at", sa.DateTime(timezone=True), nullable=True))
    op.create_index("ix_documents_document_type", "documents", ["document_type"])
    op.create_index("ix_documents_issuing_agency", "documents", ["issuing_agency"])


def downgrade() -> None:
    op.drop_index("ix_documents_issuing_agency", table_name="documents")
    op.drop_index("ix_documents_document_type", table_name="documents")
    op.drop_column("documents", "metadata_reviewed_at")
    op.drop_column("documents", "metadata_source")
    op.drop_column("documents", "page_count")
    op.drop_column("documents", "attachment_present")
    op.drop_column("documents", "seals_present")
    op.drop_column("documents", "signer_title")
    op.drop_column("documents", "signer_name")
    op.drop_column("documents", "recipient")
    op.drop_column("documents", "excerpt")
    op.drop_column("documents", "issued_place")
    op.drop_column("documents", "document_symbol")
    op.drop_column("documents", "classification_confidence")
