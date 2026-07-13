"""Serial Number Generator —— 单据编号生成接口（Protocol）

M1 仅定义接口，具体实现（数据库序列、Redis 自增等）在业务模块中注入。

编号格式: {prefix}-{date:%Y%m%d}-{seq:03d}
示例: PO-20260707-001

不同模块可使用不同生成策略（按日重置、按月重置、全局递增等）。
"""

from datetime import date
from typing import Protocol


class SerialNumberGenerator(Protocol):
    """单据编号生成器接口

    使用示例::

        serial = di.get("serial_number_generator")
        order_no = await serial.generate("PO")  # → "PO-20260707-001"
        order_no = await serial.generate("SO", seq_length=4)  # → "SO-20260707-0001"
    """

    async def generate(
        self,
        prefix: str,
        *,
        date: date | None = None,
        seq_length: int = 3,
    ) -> str:
        """生成单据编号

        Args:
            prefix: 前缀，例如 "PO"、"SO"、"INV"
            date: 日期，默认当天
            seq_length: 序列号位数，默认 3（001-999）

        Returns:
            格式为 "{prefix}-{YYYYmmdd}-{seq}" 的编号
        """
        ...
