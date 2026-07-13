"""Serial Number 序列号模块 —— M1 仅定义接口

后续提供数据库序列、Redis 自增等具体实现。
"""

from app.shared.serial_number.registry import SerialNumberGenerator

__all__ = [
    "SerialNumberGenerator",
]
