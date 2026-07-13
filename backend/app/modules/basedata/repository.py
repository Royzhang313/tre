"""基础资料 —— Repository（SaaS 多租户版）

所有查询强制按 tenant_id 过滤，实现行级数据隔离。
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.modules.basedata.models import CommissionPlatform, Company, Enterprise, Warehouse
from app.shared.base_repository import BaseRepository


class EnterpriseRepository(BaseRepository[Enterprise]):
    def __init__(self, session: AsyncSession):
        super().__init__(Enterprise, session, entity_name="企业")

    async def get_with_contacts(self, enterprise_id: UUID, tenant_id: UUID | None = None) -> Enterprise | None:
        stmt = (
            select(Enterprise).where(Enterprise.id == enterprise_id)
            .options(selectinload(Enterprise.contacts))
        )
        if tenant_id:
            stmt = stmt.where(Enterprise.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return r.scalar_one_or_none()

    async def list_all(self, tenant_id: UUID | None = None) -> list[Enterprise]:
        stmt = (
            select(Enterprise).options(selectinload(Enterprise.contacts))
            .where(Enterprise.is_active == True)
            .order_by(Enterprise.created_at.desc())
        )
        if tenant_id:
            stmt = stmt.where(Enterprise.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())

    async def list_deleted(self, tenant_id: UUID | None = None) -> list[Enterprise]:
        """查询已删除（停用）的企业"""
        stmt = (
            select(Enterprise).options(selectinload(Enterprise.contacts))
            .where(Enterprise.is_active == False)
            .order_by(Enterprise.updated_at.desc())
        )
        if tenant_id:
            stmt = stmt.where(Enterprise.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())


class CompanyRepository(BaseRepository[Company]):
    def __init__(self, session: AsyncSession):
        super().__init__(Company, session, entity_name="主体公司")

    async def get_by_name(self, name: str, tenant_id: UUID | None = None) -> Company | None:
        """按名称查找公司（用于去重校验，租户内唯一）"""
        stmt = select(Company).where(Company.name == name)
        if tenant_id:
            stmt = stmt.where(Company.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return r.scalar_one_or_none()

    async def list_active(self, tenant_id: UUID | None = None) -> list[Company]:
        stmt = select(Company).where(Company.is_active == True).order_by(Company.created_at.desc())
        if tenant_id:
            stmt = stmt.where(Company.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())

    async def list_deleted(self, tenant_id: UUID | None = None) -> list[Company]:
        stmt = select(Company).where(Company.is_active == False).order_by(Company.updated_at.desc())
        if tenant_id:
            stmt = stmt.where(Company.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return list(r.scalars().all())


class WarehouseRepository(BaseRepository[Warehouse]):
    def __init__(self, session: AsyncSession):
        super().__init__(Warehouse, session, entity_name="仓库")


class CommissionPlatformRepository(BaseRepository[CommissionPlatform]):
    def __init__(self, session: AsyncSession):
        super().__init__(CommissionPlatform, session, entity_name="撮合平台")

    async def get_by_name(self, name: str, tenant_id: UUID | None = None) -> CommissionPlatform | None:
        """按名称查找撮合平台（用于去重校验，租户内唯一）"""
        stmt = select(CommissionPlatform).where(CommissionPlatform.name == name)
        if tenant_id:
            stmt = stmt.where(CommissionPlatform.tenant_id == tenant_id)
        r = await self.session.execute(stmt)
        return r.scalar_one_or_none()
