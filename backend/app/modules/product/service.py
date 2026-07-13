"""产品模块 —— Service 层"""

from uuid import UUID

from app.core.exceptions import ConflictError
from app.modules.product.models import Product
from app.modules.product.repository import ProductRepository
from app.modules.product.schemas import ProductCreate, ProductUpdate
from app.shared.audit_helper import audit_record, orm_to_dict


class ProductService:
    def __init__(self, repo: ProductRepository):
        self.repo = repo

    async def create(self, data: ProductCreate) -> Product:
        """创建产品 —— 校验产品编码唯一"""
        existing = await self.repo.get_by_product_code(data.product_code)
        if existing:
            raise ConflictError(
                f"产品编码 '{data.product_code}' 已存在", entity="Product"
            )
        obj = Product(**data.model_dump())
        await self.repo.create(obj)
        await audit_record(
            session=self.repo.session,
            action="create",
            entity_type="product",
            entity_id=obj.id,
            after=orm_to_dict(obj),
        )
        return obj

    async def update(self, obj_id: UUID, data: ProductUpdate) -> Product:
        """更新产品 —— 校验编码唯一（如变更）"""
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        update_dict = data.model_dump(exclude_unset=True)
        if "product_code" in update_dict and update_dict["product_code"] != obj.product_code:
            existing = await self.repo.get_by_product_code(update_dict["product_code"])
            if existing and existing.id != obj_id:
                raise ConflictError(
                    f"产品编码 '{update_dict['product_code']}' 已存在", entity="Product"
                )
        for k, v in update_dict.items():
            setattr(obj, k, v)
        await self.repo.update(obj)
        await audit_record(
            session=self.repo.session,
            action="update",
            entity_type="product",
            entity_id=obj.id,
            before=before,
            after=orm_to_dict(obj),
        )
        return obj

    async def delete(self, obj_id: UUID) -> None:
        """停用产品（软删除）"""
        obj = await self.repo.get_by_id_or_raise(obj_id)
        before = orm_to_dict(obj)
        obj.is_active = False
        await self.repo.update(obj)
        await audit_record(
            session=self.repo.session,
            action="delete",
            entity_type="product",
            entity_id=obj.id,
            before=before,
        )
