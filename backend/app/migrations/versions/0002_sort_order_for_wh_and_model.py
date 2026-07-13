"""add sort_order to brand_warehouses and brand_models

Revision ID: 0002
Revises: 0001
Create Date: 2026-07-10
"""
from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 品牌仓库加 sort_order
    op.add_column("brand_warehouses", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))
    # 品牌型号加 sort_order
    op.add_column("brand_models", sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"))


def downgrade() -> None:
    with op.batch_alter_table("brand_models") as batch_op:
        batch_op.drop_column("sort_order")
    with op.batch_alter_table("brand_warehouses") as batch_op:
        batch_op.drop_column("sort_order")
