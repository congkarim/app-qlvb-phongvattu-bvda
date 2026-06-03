"""add OCR job type and reason

Revision ID: 0003_ocr_job_type
Revises: 0002_chunk_text_trgm
Create Date: 2026-06-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0003_ocr_job_type"
down_revision: str | None = "0002_chunk_text_trgm"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ocr_jobs", sa.Column("job_type", sa.String(length=64), nullable=False, server_default="ocr"))
    op.add_column("ocr_jobs", sa.Column("reason", sa.Text(), nullable=True))
    op.alter_column("ocr_jobs", "job_type", server_default=None)


def downgrade() -> None:
    op.drop_column("ocr_jobs", "reason")
    op.drop_column("ocr_jobs", "job_type")
