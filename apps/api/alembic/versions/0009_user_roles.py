"""add user roles

Revision ID: 0009_user_roles
Revises: 0008_document_chunk_metadata
Create Date: 2026-06-04
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0009_user_roles"
down_revision: str | None = "0008_document_chunk_metadata"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("role", sa.String(length=32), nullable=False, server_default="user"))
    op.execute("UPDATE users SET role = 'admin' WHERE email = 'admin@example.com'")
    op.alter_column("users", "role", server_default=None)
    op.create_index("ix_users_role", "users", ["role"])


def downgrade() -> None:
    op.drop_index("ix_users_role", table_name="users")
    op.drop_column("users", "role")
