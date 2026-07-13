"""产品模块 —— Repository 层"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.product.models import Product
from app.shared.base_repository import BaseRepository


class ProductRepository(BaseRepository[Product]):
    def __init__(self, session: AsyncSession):
        super().__init__(Product, session, entity_name="产品")

    async def get_by_product_code(self, code: str) -> Product | None:
        """按产品编码查找（用于去重校验）"""
        stmt = select(Product).where(Product.product_code == code)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_active(
        self, offset: int = 0, limit: int = 20
    ) -> list[Product]:
        """分页查询启用中的产品"""
        stmt = (
            select(Product)
            .where(Product.is_active == True)
            .order_by(Product.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def list_all_with_filters(
        self,
        offset: int = 0,
        limit: int = 20,
        search: str | None = None,
        model_type: str | None = None,
        is_active: bool | None = None,
    ) -> list[Product]:
        """支持多条件筛选的产品列表"""
        stmt = select(Product)
        if search:
            stmt = stmt.where(
                (Product.name.ilike(f"%{search}%"))
                | (Product.product_code.ilike(f"%{search}%"))
                | (Product.brand_name.ilike(f"%{search}%"))
            )
        if model_type:
            stmt = stmt.where(Product.model_type == model_type)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
        stmt = stmt.order_by(Product.created_at.desc()).offset(offset).limit(limit)
        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def count_with_filters(
        self,
        search: str | None = None,
        model_type: str | None = None,
        is_active: bool | None = None,
    ) -> int:
        """按筛选条件统计产品数量"""
        from sqlalchemy import func

        stmt = select(func.count()).select_from(Product)
        if search:
            stmt = stmt.where(
                (Product.name.ilike(f"%{search}%"))
                | (Product.product_code.ilike(f"%{search}%"))
                | (Product.brand_name.ilike(f"%{search}%"))
            )
        if model_type:
            stmt = stmt.where(Product.model_type == model_type)
        if is_active is not None:
            stmt = stmt.where(Product.is_active == is_active)
        result = await self.session.execute(stmt)
        return result.scalar_one()
