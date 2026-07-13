"""品牌模块 —— Service（含审计日志）"""

from uuid import UUID

from app.core.exceptions import ConflictError
from app.modules.brand.models import Brand, BrandModel, BrandWarehouse
from app.modules.brand.repository import BrandModelRepository, BrandRepository, BrandWarehouseRepository
from app.modules.brand.schemas import BrandCreate, BrandModelCreate, BrandUpdate, BrandWarehouseCreate
from app.shared.audit_helper import audit_record, orm_to_dict


class BrandService:
    def __init__(self, repo: BrandRepository):
        self.repo = repo

    async def create(self, data: BrandCreate) -> Brand:
        if await self.repo.get_by_name(data.name):
            raise ConflictError("品牌名称已存在", entity="Brand")
        max_order = await self.repo.get_max_sort_order()
        obj = await self.repo.create(Brand(name=data.name, color=data.color, sort_order=max_order + 1))
        await audit_record(session=self.repo.session, action="create", entity_type="brand", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: BrandUpdate) -> Brand:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        for k, v in data.model_dump(exclude_unset=True).items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="brand", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def soft_delete(self, obj_id: UUID) -> None:
        """逻辑删除品牌及其子数据（被引用时禁止删除）"""
        obj = await self.repo.get_with_relations(obj_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("品牌不存在", entity="Brand", entity_id=obj_id)
        ref = await self.repo.check_brand_referenced(obj_id)
        if ref:
            raise ConflictError(f"该品牌已被{ref}引用，无法删除", entity="Brand")
        before = orm_to_dict(obj)
        obj.is_active = False
        for bw in obj.warehouses:
            bw.is_active = False
        for bm in obj.models:
            bm.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="brand", entity_id=obj.id, before=before)


class BrandWarehouseService:
    def __init__(self, repo: BrandWarehouseRepository):
        self.repo = repo

    async def create(self, data: BrandWarehouseCreate) -> BrandWarehouse:
        existing = await self.repo.list_active_by_brand(data.brand_id)
        if any(bw.name == data.name for bw in existing):
            raise ConflictError("该仓库名称已存在", entity="BrandWarehouse")
        max_order = await self.repo.get_max_sort_order(data.brand_id)
        obj = await self.repo.create(BrandWarehouse(brand_id=data.brand_id, name=data.name, sort_order=max_order + 1))
        await audit_record(session=self.repo.session, action="create", entity_type="brand_warehouse", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: dict) -> BrandWarehouse:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        for k, v in data.items():
            if v is not None: setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="brand_warehouse", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def soft_delete(self, obj_id: UUID) -> None:
        """逻辑删除仓库（被引用时禁止删除）"""
        obj = await self.repo.get_by_id_or_raise(obj_id)
        ref = await self.repo.check_warehouse_referenced(obj_id)
        if ref:
            raise ConflictError(f"该仓库已被{ref}引用，无法删除", entity="BrandWarehouse")
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="brand_warehouse", entity_id=obj.id, before=before)


class BrandModelService:
    def __init__(self, repo: BrandModelRepository):
        self.repo = repo

    async def create(self, data: BrandModelCreate) -> BrandModel:
        existing = await self.repo.list_active_by_brand(data.brand_id)
        if any(bm.model_name == data.model_name for bm in existing):
            raise ConflictError("该型号名称已存在", entity="BrandModel")
        max_order = await self.repo.get_max_sort_order(data.brand_id)
        m = BrandModel(**data.model_dump())
        m.sort_order = max_order + 1
        obj = await self.repo.create(m)
        await audit_record(session=self.repo.session, action="create", entity_type="brand_model", entity_id=obj.id, after=orm_to_dict(obj))
        return obj

    async def update(self, obj_id: UUID, data: dict) -> BrandModel:
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        for k, v in data.items():
            if v is not None:
                setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="update", entity_type="brand_model", entity_id=obj.id, before=before, after=orm_to_dict(obj))
        return obj

    async def soft_delete(self, obj_id: UUID) -> None:
        """逻辑删除型号（被引用时禁止删除）"""
        obj = await self.repo.get_by_id_or_raise(obj_id)
        ref = await self.repo.check_model_referenced(obj_id)
        if ref:
            raise ConflictError(f"该型号已被{ref}引用，无法删除", entity="BrandModel")
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="delete", entity_type="brand_model", entity_id=obj.id, before=before)
