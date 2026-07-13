"""泛型仓储基类

封装标准 CRUD 操作，所有模块的 Repository 继承此类。

Repository 保持基础设施定位：
- 接受 SQLAlchemy 查询条件（*filters），不依赖业务 FilterSchema
- FilterSchema → 查询条件的转换在 Service 层完成

使用示例::

    class ProductRepository(BaseRepository[Product]):
        async def find_active(self) -> list[Product]:
            return await self.list(filters=(Product.status == "active",))
"""

from typing import TypeVar
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.shared.base_model import BaseModel

T = TypeVar("T", bound=BaseModel)


class BaseRepository[T: BaseModel]:
    """泛型仓储基类

    Args:
        model: ORM 模型类
        session: SQLAlchemy AsyncSession
        entity_name: 实体中文名（用于错误消息），默认 "资源"
    """

    def __init__(self, model: type[T], session: AsyncSession, *, entity_name: str = "资源"):
        self.model = model
        self.session = session
        self.entity_name = entity_name

    # ============================================================
    # 查询
    # ============================================================

    async def get_by_id(self, entity_id: UUID) -> T | None:
        """按主键查询单个实体"""
        return await self.session.get(self.model, entity_id)

    async def get_by_id_or_raise(self, entity_id: UUID) -> T:
        """按 ID 查询，不存在则抛出 NotFoundError"""
        entity = await self.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(
                f"{self.entity_name}不存在",
                entity=self.entity_name,
                entity_id=entity_id,
            )
        return entity

    async def exists(self, entity_id: UUID) -> bool:
        """检查实体是否存在"""
        entity = await self.get_by_id(entity_id)
        return entity is not None

    async def list(
        self,
        *,
        offset: int = 0,
        limit: int = 20,
        order_by: str | None = None,
        filters: tuple | None = None,
    ) -> list[T]:
        """分页查询实体列表

        Args:
            offset: 跳过记录数
            limit: 返回记录数上限
            order_by: 排序字段名（默认按 created_at 降序）
            filters: SQLAlchemy 查询条件元组，例如 (Product.status == "active",)
        """
        stmt = select(self.model)

        # 应用过滤条件
        if filters:
            stmt = stmt.where(*filters)

        # 排序
        if order_by:
            column = getattr(self.model, order_by, None)
            if column is not None:
                stmt = stmt.order_by(column.desc())
        else:
            stmt = stmt.order_by(self.model.created_at.desc())  # type: ignore[union-attr]

        stmt = stmt.offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count(self, filters: tuple | None = None) -> int:
        """查询总记录数

        Args:
            filters: 可选 SQLAlchemy 查询条件
        """
        stmt = select(func.count()).select_from(self.model)
        if filters:
            stmt = stmt.where(*filters)
        result = await self.session.execute(stmt)
        return result.scalar_one()

    # ============================================================
    # 写入
    # ============================================================

    async def create(self, entity: T) -> T:
        """新增实体"""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def update(self, entity: T) -> T:
        """更新实体 —— 需要先查出来修改，然后调用此方法 flush"""
        self.session.add(entity)
        await self.session.flush()
        return entity

    async def delete(self, entity: T) -> None:
        """物理删除实体"""
        await self.session.delete(entity)
        await self.session.flush()
