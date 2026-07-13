"""基础资料 —— Service（SaaS 多租户版）

所有业务操作均需传入 tenant_id，确保数据隔离。
"""

from uuid import UUID

from app.core.exceptions import ConflictError
from app.modules.basedata.models import CommissionPlatform, Company, Enterprise, EnterpriseContact, Warehouse
from app.modules.basedata.repository import CommissionPlatformRepository, CompanyRepository, EnterpriseRepository, WarehouseRepository
from app.modules.basedata.schemas import CommissionPlatformCreate, CommissionPlatformUpdate, CompanyCreate, CompanyUpdate, EnterpriseCreate, EnterpriseUpdate, WarehouseCreate, WarehouseUpdate
from app.shared.audit_helper import audit_record, orm_to_dict


class EnterpriseService:
    def __init__(self, repo: EnterpriseRepository):
        self.repo = repo

    async def create(self, data: EnterpriseCreate, tenant_id: UUID) -> Enterprise:
        contacts = data.contacts
        d = data.model_dump(exclude={"contacts"})
        obj = Enterprise(tenant_id=tenant_id, **d)
        for c in contacts:
            obj.contacts.append(EnterpriseContact(
                tenant_id=tenant_id,
                name=c.name,
                mobile=c.mobile,
            ))
        await self.repo.create(obj)
        await audit_record(session=self.repo.session, action="create", entity_type="enterprise", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: EnterpriseUpdate, tenant_id: UUID) -> Enterprise:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="enterprise", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def delete(self, obj_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="enterprise", entity_id=obj.id, before=before)


class CompanyService:
    def __init__(self, repo: CompanyRepository):
        self.repo = repo

    async def create(self, data: CompanyCreate, tenant_id: UUID) -> Company:
        existing = await self.repo.get_by_name(data.name, tenant_id)
        if existing:
            raise ConflictError(f"主体公司 '{data.name}' 已存在", entity="Company")
        obj = Company(tenant_id=tenant_id, **data.model_dump())
        await self.repo.create(obj)
        await audit_record(session=self.repo.session, action="create", entity_type="company", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: CompanyUpdate, tenant_id: UUID) -> Company:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        if data.name and data.name != obj.name:
            existing = await self.repo.get_by_name(data.name, tenant_id)
            if existing:
                raise ConflictError(f"主体公司 '{data.name}' 已存在", entity="Company")
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="company", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def delete(self, obj_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="company", entity_id=obj.id, before=before)


class WarehouseService:
    def __init__(self, repo: WarehouseRepository):
        self.repo = repo

    async def create(self, data: WarehouseCreate, tenant_id: UUID) -> Warehouse:
        obj = Warehouse(tenant_id=tenant_id, **data.model_dump())
        await self.repo.create(obj)
        await audit_record(session=self.repo.session, action="create", entity_type="warehouse", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: WarehouseUpdate) -> Warehouse:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="warehouse", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def delete(self, obj_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="warehouse", entity_id=obj.id, before=before)


class CommissionPlatformService:
    def __init__(self, repo: CommissionPlatformRepository):
        self.repo = repo

    async def create(self, data: CommissionPlatformCreate, tenant_id: UUID) -> CommissionPlatform:
        existing = await self.repo.get_by_name(data.name, tenant_id)
        if existing:
            raise ConflictError(f"撮合平台 '{data.name}' 已存在", entity="CommissionPlatform")
        obj = CommissionPlatform(tenant_id=tenant_id, **data.model_dump())
        await self.repo.create(obj)
        await audit_record(session=self.repo.session, action="create", entity_type="commission_platform", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: CommissionPlatformUpdate, tenant_id: UUID) -> CommissionPlatform:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        if data.name and data.name != obj.name:
            existing = await self.repo.get_by_name(data.name, tenant_id)
            if existing:
                raise ConflictError(f"撮合平台 '{data.name}' 已存在", entity="CommissionPlatform")
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="commission_platform", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def delete(self, obj_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="commission_platform", entity_id=obj.id, before=before)
