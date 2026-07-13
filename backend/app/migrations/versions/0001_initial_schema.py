"""Initial schema with tags

Revision ID: 0001
Revises:
Create Date: 2026-07-08

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """标记为初始状态（数据库已通过 create_all 创建）"""
    pass


def downgrade() -> None:
    pass
