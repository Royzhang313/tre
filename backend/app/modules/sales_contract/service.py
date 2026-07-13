"""销售合同模块 —— Service 层"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from app.core.exceptions import ConflictError
from app.modules.sales_contract.models import ContractStatus, ContractType, SalesContract, SalesContractItem
from app.modules.sales_contract.repository import SalesContractItemRepository, SalesContractRepository
from app.modules.sales_contract.schemas import SalesContractCreate, SalesContractUpdate
from app.shared.audit_helper import audit_record, orm_to_dict

# 确保 FK 引用表已注册到 SQLAlchemy metadata
import app.modules.auth.models  # noqa: F401  (auth_users)
import app.modules.basedata.models  # noqa: F401  (basedata_enterprises, basedata_companies)
import app.modules.brand.models  # noqa: F401  (brands, brand_models, brand_warehouses)



class SalesContractService:
    def __init__(self, repo: SalesContractRepository, item_repo: SalesContractItemRepository):
        self.repo = repo; self.item_repo = item_repo

    async def create(self, data: SalesContractCreate, user_id: UUID, tenant_id: UUID) -> SalesContract:
        # 自动生成合同编号: {type}{YYYYMMDDhhmmss}
        type_code = data.contract_type or "SH"
        contract_no = f"{type_code}{datetime.now().strftime('%Y%m%d%H%M%S')}"
        while await self.repo.get_by_contract_no(contract_no):
            contract_no = f"{type_code}{datetime.now().strftime('%Y%m%d%H%M%S')}"

        total_qty = Decimal("0"); total_amt = Decimal("0")
        for it in data.items:
            total_qty += it.quantity
            total_amt += it.quantity * it.sale_price

        contract = SalesContract(
            tenant_id=tenant_id, company_id=data.company_id, contract_no=contract_no,
            contract_type=ContractType(type_code),
            sales_person_id=data.sales_person_id,
            customer_enterprise_id=data.customer_enterprise_id,
            commission_platform_id=data.commission_platform_id,
            contract_date=data.contract_date,
            contract_start_date=data.contract_start_date,
            contract_end_date=data.contract_end_date,
            attachment_path=data.attachment_path,
            status=ContractStatus.PENDING,
            total_quantity=total_qty, total_amount=total_amt,
            remark=data.remark, tags=data.tags, created_by=user_id,
        )
        await self.repo.create(contract)

        for i, it in enumerate(data.items, 1):
            item = SalesContractItem(
                contract_id=contract.id, line_no=i,
                brand_id=it.brand_id, model_id=it.model_id,
                shipping_warehouse_id=it.shipping_warehouse_id,
                quantity=it.quantity, unit=it.unit,
                sale_price=it.sale_price,
                amount=it.quantity * it.sale_price,
                tax_rate=it.tax_rate,
                storage_fee_price=it.storage_fee_price,
                commission_fee_price=it.commission_fee_price,
                commission_fee=it.commission_fee,
            )
            await self.item_repo.create(item)

        contract = await self.repo.get_with_items(contract.id) or contract
        await audit_record(session=self.repo.session, action="create", entity_type="sales_contract", entity_id=contract.id, after=orm_to_dict(contract))
        return contract

    async def update(self, contract_id: UUID, data: SalesContractUpdate) -> SalesContract:
        obj = await self.repo.get_with_items(contract_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("销售合同不存在", entity="SalesContract", entity_id=contract_id)
        before = orm_to_dict(obj)
        before["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]
        update_dict = data.model_dump(exclude_unset=True)
        items_data = update_dict.pop("items", None)

        # 更新 header 字段
        for k, v in update_dict.items():
            setattr(obj, k, v)

        # 同步明细行：原地更新已有行，新增无id行，删除不在列表中的行
        if data.items is not None:
            existing_ids = {it["id"] for it in items_data if it.get("id")}
            # 删除不在提交列表中的旧明细
            for old_it in list(obj.items):
                if old_it.id not in existing_ids:
                    obj.items.remove(old_it)
            await self.repo.session.flush()
            # 更新或新建
            item_map = {it.id: it for it in obj.items}
            for i, it in enumerate(items_data, 1):
                item_id = it.get("id")
                if item_id and item_id in item_map:
                    existing = item_map[item_id]
                    for k, v in it.items():
                        if k not in ("id", "amount") and v is not None:
                            setattr(existing, k, v)
                    existing.amount = existing.quantity * existing.sale_price
                    existing.line_no = i
                else:
                    new_item = SalesContractItem(
                        contract_id=contract_id, line_no=i,
                        brand_id=it.get("brand_id"), model_id=it.get("model_id"),
                        shipping_warehouse_id=it.get("shipping_warehouse_id"),
                        quantity=it.get("quantity"), unit=it.get("unit", "吨"),
                        sale_price=it.get("sale_price"),
                        amount=it.get("quantity", 0) * it.get("sale_price", 0),
                        tax_rate=it.get("tax_rate", 0),
                        storage_fee_price=it.get("storage_fee_price", 0),
                        commission_fee_price=it.get("commission_fee_price", 0),
                        commission_fee=it.get("commission_fee", 0),
                    )
                    self.repo.session.add(new_item)
            await self.repo.session.flush()
            tq = sum((it.quantity for it in obj.items), Decimal("0"))
            ta = sum((it.amount for it in obj.items), Decimal("0"))
            obj.total_quantity = tq
            obj.total_amount = ta

        await self.repo.update(obj)
        after = orm_to_dict(obj)
        after["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]
        await audit_record(session=self.repo.session, action="update", entity_type="sales_contract", entity_id=obj.id, before=before, after=after)
        return obj

    async def cancel(self, contract_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(contract_id)
        if obj.status == ContractStatus.CANCELLED:
            raise ConflictError("合同已作废", entity="SalesContract")
        before = orm_to_dict(obj)
        obj.status = ContractStatus.CANCELLED
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="cancel", entity_type="sales_contract", entity_id=obj.id, before=before, after=orm_to_dict(obj))

    async def delete_item(self, item_id: UUID) -> None:
        item = await self.item_repo.get_by_id_or_raise(item_id)
        cid = item.contract_id
        before = orm_to_dict(item)
        await self.item_repo.delete(item)
        await self._recalc_totals(cid)
        await audit_record(session=self.repo.session, action="delete_item", entity_type="sales_contract", entity_id=cid, before=before, remark=f"删除明细行 {item.line_no}")

    async def _recalc_totals(self, contract_id: UUID) -> None:
        contract = await self.repo.get_with_items(contract_id)
        if contract:
            tq = sum((it.quantity for it in contract.items), Decimal("0"))
            ta = sum((it.amount for it in contract.items), Decimal("0"))
            contract.total_quantity = tq; contract.total_amount = ta
            await self.repo.update(contract)
