"""Number Engine —— 业务编号生成器（数据库序列实现）

支持 PO/GR/SO 等前缀，按日重置序列号。
格式: {prefix}-{YYYYMMDD}-{seq:04d}
"""

from datetime import UTC, datetime

from sqlalchemy import Integer, String, UniqueConstraint, select
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import async_session_factory
from app.shared.base_model import BaseModel


class NumberSequence(BaseModel):
    """编号序列 —— 每个 prefix+date 一条记录"""

    __tablename__ = "shared_number_sequences"
    __table_args__ = (UniqueConstraint("prefix", "date_key", name="uq_number_seq"),)

    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    date_key: Mapped[str] = mapped_column(String(8), nullable=False)
    current_seq: Mapped[int] = mapped_column(Integer, default=0, server_default="0")


class NumberRule(BaseModel):
    """编号规则 —— 可配置的编号格式"""

    __tablename__ = "shared_number_rules"
    __table_args__ = (UniqueConstraint("prefix", name="uq_number_rule_prefix"),)

    prefix: Mapped[str] = mapped_column(String(10), nullable=False)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    date_format: Mapped[str] = mapped_column(String(10), nullable=False, default="%Y%m%d")
    seq_length: Mapped[int] = mapped_column(Integer, default=4)
    reset_period: Mapped[str] = mapped_column(String(10), nullable=False, default="daily")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")


class NumberEngine:
    """业务编号生成器 —— 线程安全，数据库自增"""

    @staticmethod
    async def generate(prefix: str, *, seq_length: int = 4, date_key: str | None = None) -> str:
        """生成编号: PO-20260707-0001

        Args:
            prefix: 前缀（PO / GR / SO / INV）
            seq_length: 序列号位数（默认 4）
            date_key: 日期（默认今天 YYYYMMDD）

        Returns:
            完整编号字符串
        """
        dk = date_key or datetime.now(UTC).strftime("%Y%m%d")

        async with async_session_factory() as session:
            stmt = select(NumberSequence).where(
                NumberSequence.prefix == prefix, NumberSequence.date_key == dk
            )
            result = await session.execute(stmt)
            seq = result.scalar_one_or_none()

            if seq is None:
                seq = NumberSequence(prefix=prefix, date_key=dk, current_seq=1)
                session.add(seq)
            else:
                seq.current_seq += 1
            await session.flush()

            return f"{prefix}-{dk}-{seq.current_seq:0{seq_length}d}"
