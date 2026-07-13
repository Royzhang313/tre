"""服务基类

封装通用 CRUD 逻辑，业务模块的 Service 继承此类。

使用示例:
    class ProductService(BaseService[Product]):
        async def activate(self, product_id: UUID) -> Product:
            product = await self.get_or_raise(product_id)
            ...
"""

from uuid import UUID

from app.core.exceptions import NotFoundError
from app.shared.base_model import BaseModel
from app.shared.base_repository import BaseRepository

T = BaseModel


class BaseService:
    """业务服务基类

    Args:
        repository: 对应的 Repository 实例
    """

    def __init__(self, repository: BaseRepository[T]):
        self.repository = repository

    async def get_or_raise(self, entity_id: UUID, entity_name: str = "资源") -> T:
        """按 ID 查询，不存在则抛出 NotFoundError"""
        entity = await self.repository.get_by_id(entity_id)
        if entity is None:
            raise NotFoundError(
                f"{entity_name}不存在", entity=entity_name, entity_id=entity_id
            )
        return entity

    async def get_by_id(self, entity_id: UUID) -> T | None:
        """按 ID 查询"""
        return await self.repository.get_by_id(entity_id)

    async def list(self, *, offset: int = 0, limit: int = 20) -> list[T]:
        """分页列表查询"""
        return await self.repository.list(offset=offset, limit=limit)

    async def create(self, entity: T) -> T:
        """新增"""
        return await self.repository.create(entity)

    async def update(self, entity: T) -> T:
        """更新"""
        return await self.repository.update(entity)

    async def delete(self, entity: T) -> None:
        """删除"""
        await self.repository.delete(entity)
