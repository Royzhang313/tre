"""ORM 序列化工具 —— 所有 router 统一使用此函数"""
from decimal import Decimal
from datetime import datetime
from uuid import UUID
from typing import Any


def orm_to_dict(obj: Any) -> dict:
    """将 SQLAlchemy ORM 对象转为可 JSON 序列化的 dict

    自动处理 UUID、Decimal、datetime 类型转换。
    所有 router 统一使用此函数，不再各自重复定义。
    """
    result: dict = {}
    for col in obj.__table__.columns:
        val = getattr(obj, col.name)
        if isinstance(val, UUID):
            val = str(val)
        elif isinstance(val, Decimal):
            val = float(val)
        elif isinstance(val, datetime):
            val = val.isoformat()
        elif isinstance(val, list):
            val = val
        result[col.name] = val
    return result
