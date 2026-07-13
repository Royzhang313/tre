"""审计辅助 —— 将 ORM 对象序列化为字典并记录审计日志"""

from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.audit_engine import AuditEngine


def _serialize(val):
    """将字段值转为 JSON 可序列化类型"""
    if isinstance(val, UUID):
        return str(val)
    if isinstance(val, Decimal):
        return float(val)
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, date):
        return val.isoformat()
    if isinstance(val, list):
        return [_serialize(v) for v in val]
    if isinstance(val, dict):
        return {k: _serialize(v) for k, v in val.items()}
    return val


def orm_to_dict(obj) -> dict:
    """将 ORM 对象转为普通 dict —— 遍历 __table__.columns 和关系字段"""
    result = {}
    for col in obj.__table__.columns:
        result[col.name] = _serialize(getattr(obj, col.name))
    return result


async def audit_record(
    *,
    session: AsyncSession | None = None,
    action: str,
    entity_type: str,
    entity_id: UUID,
    before: dict | None = None,
    after: dict | None = None,
    remark: str | None = None,
):
    """记录审计日志（fire-and-forget，失败不影响主流程）

    Args:
        session: 可选，复用已有 session（推荐，避免 SQLite 锁竞争）
    """
    try:
        await AuditEngine.record(
            session=session,
            action=action,
            entity_type=entity_type,
            entity_id=entity_id,
            before=before,
            after=after,
            remark=remark,
        )
    except Exception:
        pass  # 审计失败不影响主流程
