"""add admin catalogs

Revision ID: 0012_admin_catalogs
Revises: 0011_contract_records
Create Date: 2026-06-06
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0012_admin_catalogs"
down_revision: str | None = "0011_contract_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


BUSINESS_TYPE_SEEDS = [
    ("10000000-0000-0000-0000-000000000001", "business_type", "incoming_dispatch", "Công văn đến", 10),
    ("10000000-0000-0000-0000-000000000002", "business_type", "outgoing_dispatch", "Công văn đi", 20),
    ("10000000-0000-0000-0000-000000000003", "business_type", "contract", "Hợp đồng", 30),
    ("10000000-0000-0000-0000-000000000004", "business_type", "decision", "Quyết định", 40),
]

DOCUMENT_TYPE_SEEDS = [
    ("20000000-0000-0000-0000-000000000001", "UNKNOWN", "Không đủ dữ liệu"),
    ("20000000-0000-0000-0000-000000000002", "NQ", "Nghị quyết"),
    ("20000000-0000-0000-0000-000000000003", "QĐ", "Quyết định"),
    ("20000000-0000-0000-0000-000000000004", "CT", "Chỉ thị"),
    ("20000000-0000-0000-0000-000000000005", "QC", "Quy chế"),
    ("20000000-0000-0000-0000-000000000006", "QYĐ", "Quy định"),
    ("20000000-0000-0000-0000-000000000007", "TC", "Thông cáo"),
    ("20000000-0000-0000-0000-000000000008", "TB", "Thông báo"),
    ("20000000-0000-0000-0000-000000000009", "HD", "Hướng dẫn"),
    ("20000000-0000-0000-0000-000000000010", "CTr", "Chương trình"),
    ("20000000-0000-0000-0000-000000000011", "KH", "Kế hoạch"),
    ("20000000-0000-0000-0000-000000000012", "PA", "Phương án"),
    ("20000000-0000-0000-0000-000000000013", "ĐA", "Đề án"),
    ("20000000-0000-0000-0000-000000000014", "DA", "Dự án"),
    ("20000000-0000-0000-0000-000000000015", "BC", "Báo cáo"),
    ("20000000-0000-0000-0000-000000000016", "BB", "Biên bản"),
    ("20000000-0000-0000-0000-000000000017", "TTr", "Tờ trình"),
    ("20000000-0000-0000-0000-000000000018", "HĐ", "Hợp đồng"),
    ("20000000-0000-0000-0000-000000000019", "CV", "Công văn"),
    ("20000000-0000-0000-0000-000000000020", "CĐ", "Công điện"),
    ("20000000-0000-0000-0000-000000000021", "BGN", "Bản ghi nhớ"),
    ("20000000-0000-0000-0000-000000000022", "BTT", "Bản thỏa thuận"),
    ("20000000-0000-0000-0000-000000000023", "GUQ", "Giấy ủy quyền"),
    ("20000000-0000-0000-0000-000000000024", "GM", "Giấy mời"),
    ("20000000-0000-0000-0000-000000000025", "GGT", "Giấy giới thiệu"),
    ("20000000-0000-0000-0000-000000000026", "GNP", "Giấy nghỉ phép"),
    ("20000000-0000-0000-0000-000000000027", "PG", "Phiếu gửi"),
    ("20000000-0000-0000-0000-000000000028", "PC", "Phiếu chuyển"),
    ("20000000-0000-0000-0000-000000000029", "PB", "Phiếu báo"),
    ("20000000-0000-0000-0000-000000000030", "TCg", "Thư công"),
]


def upgrade() -> None:
    uuid_type = postgresql.UUID(as_uuid=False)

    op.add_column("departments", sa.Column("description", sa.Text(), nullable=True))
    op.add_column("departments", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("departments", sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.alter_column("departments", "sort_order", server_default=None)
    op.alter_column("departments", "is_active", server_default=None)
    op.drop_constraint("departments_code_key", "departments", type_="unique")
    op.drop_constraint("departments_name_key", "departments", type_="unique")
    op.create_index(
        "ux_departments_code_active",
        "departments",
        ["code"],
        unique=True,
        postgresql_where=sa.text("code IS NOT NULL AND deleted_at IS NULL"),
    )
    op.create_index(
        "ux_departments_name_active",
        "departments",
        ["name"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index("ix_departments_active_sort", "departments", ["is_active", "sort_order"])

    op.create_table(
        "admin_catalog_items",
        sa.Column("catalog_type", sa.String(length=64), nullable=False),
        sa.Column("code", sa.String(length=64), nullable=False),
        sa.Column("label", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("id", uuid_type, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.alter_column("admin_catalog_items", "sort_order", server_default=None)
    op.alter_column("admin_catalog_items", "is_active", server_default=None)
    op.create_index(
        "ux_admin_catalog_items_type_code_active",
        "admin_catalog_items",
        ["catalog_type", "code"],
        unique=True,
        postgresql_where=sa.text("deleted_at IS NULL"),
    )
    op.create_index(
        "ix_admin_catalog_items_type_active_sort",
        "admin_catalog_items",
        ["catalog_type", "is_active", "sort_order"],
    )

    _seed_departments()
    _seed_catalog_items()


def downgrade() -> None:
    op.drop_index("ix_admin_catalog_items_type_active_sort", table_name="admin_catalog_items")
    op.drop_index("ux_admin_catalog_items_type_code_active", table_name="admin_catalog_items")
    op.drop_table("admin_catalog_items")

    op.drop_index("ix_departments_active_sort", table_name="departments")
    op.drop_index("ux_departments_name_active", table_name="departments")
    op.drop_index("ux_departments_code_active", table_name="departments")
    op.create_unique_constraint("departments_name_key", "departments", ["name"])
    op.create_unique_constraint("departments_code_key", "departments", ["code"])
    op.drop_column("departments", "is_active")
    op.drop_column("departments", "sort_order")
    op.drop_column("departments", "description")


def _seed_departments() -> None:
    op.execute(
        """
        INSERT INTO departments (id, code, name, description, sort_order, is_active, created_at, updated_at)
        SELECT '30000000-0000-0000-0000-000000000001', 'VT', 'Phòng Vật tư', 'Đơn vị mặc định cho phòng vật tư', 10, true, now(), now()
        WHERE NOT EXISTS (
            SELECT 1 FROM departments WHERE code = 'VT' AND deleted_at IS NULL
        )
        """
    )
    op.execute(
        """
        INSERT INTO departments (id, code, name, description, sort_order, is_active, created_at, updated_at)
        SELECT '30000000-0000-0000-0000-000000000002', 'UNKNOWN', 'Chưa xác định', 'Fallback khi chưa rõ đơn vị', 999, true, now(), now()
        WHERE NOT EXISTS (
            SELECT 1 FROM departments WHERE code = 'UNKNOWN' AND deleted_at IS NULL
        )
        """
    )


def _seed_catalog_items() -> None:
    catalog_table = sa.table(
        "admin_catalog_items",
        sa.column("id", postgresql.UUID(as_uuid=False)),
        sa.column("catalog_type", sa.String),
        sa.column("code", sa.String),
        sa.column("label", sa.String),
        sa.column("sort_order", sa.Integer),
        sa.column("is_active", sa.Boolean),
    )
    op.bulk_insert(
        catalog_table,
        [
            {
                "id": item_id,
                "catalog_type": catalog_type,
                "code": code,
                "label": label,
                "sort_order": sort_order,
                "is_active": True,
            }
            for item_id, catalog_type, code, label, sort_order in BUSINESS_TYPE_SEEDS
        ],
    )
    op.bulk_insert(
        catalog_table,
        [
            {
                "id": item_id,
                "catalog_type": "document_type",
                "code": code,
                "label": label,
                "sort_order": index * 10,
                "is_active": True,
            }
            for index, (item_id, code, label) in enumerate(DOCUMENT_TYPE_SEEDS, start=1)
        ],
    )
