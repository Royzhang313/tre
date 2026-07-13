"""基础资料 —— Repository"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.basedata.models import CommissionPlatform, Company, Enterprise, Warehouse
from app.shared.base_repository import BaseRepository


class EnterpriseRepository(BaseRepository[Enterprise]):
    def __init__(self, session: AsyncSession):
        super().__init__(Enterprise, session, entity_name="企业")

    async def get_with_contacts(self, enterprise_id: UUID) -> Enterprise | None:
        r = await self.session.execute(
            select(Enterprise).where(Enterprise.id == enterprise_id)
            .options(selectinload(Enterprise.contacts))
        )
        return r.scalar_one_or_none()

    async def list_all(self) -> list[Enterprise]:
        r = await self.session.execute(
            select(Enterprise).options(selectinload(Enterprise.contacts))
            .where(Enterprise.is_active == True)
            .order_by(Enterprise.created_at.desc())
        )
        return list(r.scalars().all())

    async def list_deleted(self) -> list[Enterprise]:
        """查询已删除（停用）的企业"""
        r = await self.session.execute(
            select(Enterprise).options(selectinload(Enterprise.contacts))
            .where(Enterprise.is_active == False)
            .order_by(Enterprise.updated_at.desc())
        )
        return list(r.scalars().all())


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session, entity_name="主体公司")

    async def get_by_name(self, name: str) -> Company | None:
        """按名称查找公司（用于去重校验）"""
        r = await self.session.execute(
            select(Company).where(Company.name == name)
        )
        return r.scalar_one_or_none()

    async def list_active(self) -> list[Company]:
        r = await self.session.execute(
            select(Company).where(Company.is_active == True).order_by(Company.created_at.desc())
        )
        return list(r.scalars().all())

    async def list_deleted(self) -> list[Company]:
        r = await self.session.execute(
            select(Company).where(Company.is_active == False).order_by(Company.updated_at.desc())
        )
        return list(r.scalars().all())


class WarehouseRepository(BaseRepository[Warehouse]):
    def __init__(self, session: AsyncSession):
        super().__init__(Warehouse, session, entity_name="仓库")


class CommissionPlatformRepository(BaseRepository[CommissionPlatform]):
    def __init__(self, session: AsyncSession):
        super().__init__(CommissionPlatform, session, entity_name="撮合平台")

    async def get_by_name(self, name: str) -> CommissionPlatform | None:
        """按名称查找撮合平台（用于去重校验）"""
        r = await self.session.execute(
            select(CommissionPlatform).where(CommissionPlatform.name == name)
        )
        return r.scalar_one_or_none()
