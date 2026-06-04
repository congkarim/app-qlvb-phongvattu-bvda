"""add document chunk metadata

Revision ID: 0008_document_chunk_metadata
Revises: 0007_document_ocr_metadata
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0008_document_chunk_metadata"
down_revision: str | None = "0007_document_ocr_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("document_chunks", sa.Column("doc_group", sa.String(length=8), nullable=True))
    op.add_column("document_chunks", sa.Column("chunk_level", sa.String(length=32), nullable=True))
    op.add_column("document_chunks", sa.Column("section_role", sa.String(length=64), nullable=True))
    op.add_column("document_chunks", sa.Column("section_path", sa.JSON(), nullable=True))
    op.add_column("document_chunks", sa.Column("chunk_confidence", sa.Float(), nullable=True))
    op.add_column(
        "document_chunks",
        sa.Column("requires_review", sa.Boolean(), nullable=False, server_default=sa.false()),
    )
    op.alter_column("document_chunks", "requires_review", server_default=None)
    op.create_index("ix_document_chunks_doc_group", "document_chunks", ["doc_group"])
    op.create_index("ix_document_chunks_section_role", "document_chunks", ["section_role"])
    op.create_index("ix_document_chunks_requires_review", "document_chunks", ["requires_review"])


def downgrade() -> None:
    op.drop_index("ix_document_chunks_requires_review", table_name="document_chunks")
    op.drop_index("ix_document_chunks_section_role", table_name="document_chunks")
    op.drop_index("ix_document_chunks_doc_group", table_name="document_chunks")
    op.drop_column("document_chunks", "requires_review")
    op.drop_column("document_chunks", "chunk_confidence")
    op.drop_column("document_chunks", "section_path")
    op.drop_column("document_chunks", "section_role")
    op.drop_column("document_chunks", "chunk_level")
    op.drop_column("document_chunks", "doc_group")
