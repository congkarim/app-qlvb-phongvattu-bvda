"""add materials catalog

Revision ID: 0018_materials_catalog
Revises: 0017_procurement_line_items
Create Date: 2026-06-08
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0018_materials_catalog"
down_revision: str | None = "0017_procurement_line_items"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

SEED_VT001_ID = "20000000-0000-0000-0000-000000000001"
SEED_VT002_ID = "20000000-0000-0000-0000-000000000002"


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.create_table(
        "materials_catalog",
        sa.Column("code", sa.String(length=64), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("default_unit", sa.String(length=32), nullable=True),
        sa.Column("category", sa.String(length=128), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("materials_catalog", "is_active", server_default=None)

    op.execute(
        """
        CREATE UNIQUE INDEX ux_materials_catalog_code_active
        ON materials_catalog (lower(trim(code)))
        WHERE deleted_at IS NULL AND code IS NOT NULL AND trim(code) <> ''
        """
    )
    op.execute(
        """
        CREATE UNIQUE INDEX ux_materials_catalog_name_active
        ON materials_catalog (lower(trim(name)))
        WHERE deleted_at IS NULL
        """
    )
    op.create_index(
        "ix_materials_catalog_name_active",
        "materials_catalog",
        ["name", "deleted_at"],
    )
    op.create_index(
        "ix_materials_catalog_is_active",
        "materials_catalog",
        ["is_active", "deleted_at"],
    )

    op.add_column(
        "procurement_line_items",
        sa.Column("catalog_item_id", uuid_type, nullable=True),
    )
    op.create_foreign_key(
        "fk_procurement_line_items_catalog_item_id",
        "procurement_line_items",
        "materials_catalog",
        ["catalog_item_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_index(
        "ix_procurement_line_items_catalog_item_active",
        "procurement_line_items",
        ["catalog_item_id", "deleted_at"],
    )

    _seed_materials_catalog()


def downgrade() -> None:
    op.drop_index("ix_procurement_line_items_catalog_item_active", table_name="procurement_line_items")
    op.drop_constraint(
        "fk_procurement_line_items_catalog_item_id",
        "procurement_line_items",
        type_="foreignkey",
    )
    op.drop_column("procurement_line_items", "catalog_item_id")

    op.drop_index("ix_materials_catalog_is_active", table_name="materials_catalog")
    op.drop_index("ix_materials_catalog_name_active", table_name="materials_catalog")
    op.execute("DROP INDEX IF EXISTS ux_materials_catalog_name_active")
    op.execute("DROP INDEX IF EXISTS ux_materials_catalog_code_active")
    op.drop_table("materials_catalog")


def _seed_materials_catalog() -> None:
    op.execute(
        f"""
        INSERT INTO materials_catalog (
            id, code, name, default_unit, category, description, is_active, created_at, updated_at
        )
        SELECT
            '{SEED_VT001_ID}',
            'VT-001',
            'Giấy A4',
            'Ram',
            'Văn phòng phẩm',
            'Giấy in A4 80gsm',
            true,
            now(),
            now()
        WHERE NOT EXISTS (
            SELECT 1 FROM materials_catalog
            WHERE deleted_at IS NULL AND lower(trim(code)) = lower(trim('VT-001'))
        )
        """
    )
    op.execute(
        f"""
        INSERT INTO materials_catalog (
            id, code, name, default_unit, category, description, is_active, created_at, updated_at
        )
        SELECT
            '{SEED_VT002_ID}',
            'VT-002',
            'Mực in HP',
            'Hộp',
            'Văn phòng phẩm',
            'Mực in HP 85A',
            true,
            now(),
            now()
        WHERE NOT EXISTS (
            SELECT 1 FROM materials_catalog
            WHERE deleted_at IS NULL AND lower(trim(code)) = lower(trim('VT-002'))
        )
        """
    )
