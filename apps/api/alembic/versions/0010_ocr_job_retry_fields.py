"""add OCR job retry fields

Revision ID: 0010_ocr_job_retry_fields
Revises: 0009_user_roles
Create Date: 2026-06-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0010_ocr_job_retry_fields"
down_revision: str | None = "0009_user_roles"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("ocr_jobs", sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"))
    op.add_column("ocr_jobs", sa.Column("failed_reason", sa.String(length=128), nullable=True))
    op.add_column("ocr_jobs", sa.Column("next_run_at", sa.DateTime(timezone=True), nullable=True))
    op.alter_column("ocr_jobs", "max_attempts", server_default=None)
    op.create_index("ix_ocr_jobs_status_next_run", "ocr_jobs", ["status", "next_run_at", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_ocr_jobs_status_next_run", table_name="ocr_jobs")
    op.drop_column("ocr_jobs", "next_run_at")
    op.drop_column("ocr_jobs", "failed_reason")
    op.drop_column("ocr_jobs", "max_attempts")
