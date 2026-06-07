"""add document relations

Revision ID: 0016_document_relations
Revises: 0015_procurement_records
Create Date: 2026-06-07
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0016_document_relations"
down_revision: str | None = "0015_procurement_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "document_relations",
        sa.Column("source_document_id", uuid_type, nullable=False),
        sa.Column("target_document_id", uuid_type, nullable=False),
        sa.Column("relation_type", sa.String(length=32), nullable=False),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by_user_id", uuid_type, nullable=True),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint(
            "source_document_id <> target_document_id",
            name="ck_document_relations_no_self_link",
        ),
        sa.ForeignKeyConstraint(["created_by_user_id"], ["users.id"]),
        sa.ForeignKeyConstraint(["source_document_id"], ["documents.id"]),
        sa.ForeignKeyConstraint(["target_document_id"], ["documents.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ux_document_relations_active_triple",
        "document_relations",
        ["source_document_id", "target_document_id", "relation_type"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_document_relations_source_active",
        "document_relations",
        ["source_document_id", "deleted_at"],
    )
    op.create_index(
        "ix_document_relations_target_active",
        "document_relations",
        ["target_document_id", "deleted_at"],
    )
    op.create_index(
        "ix_document_relations_type_active",
        "document_relations",
        ["relation_type", "deleted_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_document_relations_type_active", table_name="document_relations")
    op.drop_index("ix_document_relations_target_active", table_name="document_relations")
    op.drop_index("ix_document_relations_source_active", table_name="document_relations")
    op.drop_index("ux_document_relations_active_triple", table_name="document_relations")
    op.drop_table("document_relations")
