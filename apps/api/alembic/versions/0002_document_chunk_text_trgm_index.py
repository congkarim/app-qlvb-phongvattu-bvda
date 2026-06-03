"""add trigram index for document chunk text

Revision ID: 0002_chunk_text_trgm
Revises: 0001_initial_schema
Create Date: 2026-06-03
"""

from collections.abc import Sequence

from alembic import op

revision: str = "0002_chunk_text_trgm"
down_revision: str | None = "0001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_document_chunks_text_trgm "
        "ON document_chunks USING gin (text gin_trgm_ops) "
        "WHERE deleted_at IS NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_document_chunks_text_trgm")
