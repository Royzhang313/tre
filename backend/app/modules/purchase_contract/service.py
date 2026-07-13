"""采购合同模块 —— Service 层 V2"""

from decimal import Decimal
from uuid import UUID

from app.core.exceptions import ConflictError
from app.modules.purchase_contract.models import ContractStatus, PurchaseContract, PurchaseContractItem
from app.modules.purchase_contract.repository import PurchaseContractItemRepository, PurchaseContractRepository
from app.modules.purchase_contract.schemas import PurchaseContractCreate, PurchaseContractUpdate
from app.shared.audit_helper import audit_record, orm_to_dict

# 确保 FK 引用表已注册到 SQLAlchemy metadata
import app.modules.auth.models  # noqa: F401  (auth_users)
import app.modules.basedata.models  # noqa: F401  (basedata_enterprises, basedata_companies)
import app.modules.brand.models  # noqa: F401  (brands, brand_models, brand_warehouses)



class PurchaseContractService:
    def __init__(self, repo: PurchaseContractRepository, item_repo: PurchaseContractItemRepository):
        self.repo = repo; self.item_repo = item_repo

    async def create(self, data: PurchaseContractCreate, user_id: UUID, tenant_id: UUID) -> PurchaseContract:
        # 校验合同编号唯一
        if await self.repo.get_by_contract_no(data.contract_no):
            raise ConflictError(f"合同编号 '{data.contract_no}' 已存在", entity="PurchaseContract")

        total_qty = Decimal("0"); total_amt = Decimal("0")
        for it in data.items:
            total_qty += it.quantity
            total_amt += it.quantity * it.purchase_price

        contract = PurchaseContract(
            tenant_id=tenant_id, company_id=data.company_id, contract_no=data.contract_no,
            supplier_enterprise_id=data.supplier_enterprise_id,
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
            item = PurchaseContractItem(
                contract_id=contract.id, line_no=i,
                brand_id=it.brand_id, model_id=it.model_id,
                shipping_warehouse_id=it.shipping_warehouse_id,
                quantity=it.quantity, unit=it.unit,
                purchase_price=it.purchase_price,
                amount=it.quantity * it.purchase_price,
                tax_rate=it.tax_rate,
                storage_fee_price=it.storage_fee_price,
                commission_fee_price=it.commission_fee_price,
                commission_fee=it.commission_fee,
            )
            await self.item_repo.create(item)

        contract = await self.repo.get_with_items(contract.id) or contract
        await audit_record(session=self.repo.session, action="create", entity_type="purchase_contract", entity_id=contract.id, after=orm_to_dict(contract))
        return contract

    async def update(self, contract_id: UUID, data: PurchaseContractUpdate) -> PurchaseContract:
        obj = await self.repo.get_with_items(contract_id)
        if not obj:
            from app.core.exceptions import NotFoundError
            raise NotFoundError("采购合同不存在", entity="PurchaseContract", entity_id=contract_id)
        before = orm_to_dict(obj)
        before["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]
        update_dict = data.model_dump(exclude_unset=True)
        items_data = update_dict.pop("items", None)

        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"[UPDATE] contract_id={contract_id}, update_keys={list(update_dict.keys())}, items_data={'None' if items_data is None else f'list[{len(items_data)}]'}, data.items={'None' if data.items is None else f'list[{len(data.items)}]'}")

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
                    # 原地更新
                    existing = item_map[item_id]
                    for k, v in it.items():
                        if k not in ("id", "amount") and v is not None:
                            setattr(existing, k, v)
                    existing.amount = existing.quantity * existing.purchase_price
                    existing.line_no = i
                else:
                    # 新建
                    new_item = PurchaseContractItem(
                        contract_id=contract_id, line_no=i,
                        brand_id=it.get("brand_id"), model_id=it.get("model_id"),
                        shipping_warehouse_id=it.get("shipping_warehouse_id"),
                        quantity=it.get("quantity"), unit=it.get("unit", "吨"),
                        purchase_price=it.get("purchase_price"),
                        amount=it.get("quantity", 0) * it.get("purchase_price", 0),
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
            logger.warning(f"[UPDATE] after_items: total_qty={tq}, item_count={len(obj.items)}")

        await self.repo.update(obj)
        logger.warning(f"[UPDATE] saved: remark={obj.remark}, total={obj.total_quantity}")
        after = orm_to_dict(obj)
        after["items"] = [{k: v for k, v in orm_to_dict(it).items()} for it in obj.items]
        await audit_record(session=self.repo.session, action="update", entity_type="purchase_contract", entity_id=obj.id, before=before, after=after)
        return obj

    async def cancel(self, contract_id: UUID) -> None:
        obj = await self.repo.get_by_id_or_raise(contract_id)
        if obj.status == ContractStatus.CANCELLED:
            raise ConflictError("合同已作废", entity="PurchaseContract")
        before = orm_to_dict(obj)
        obj.status = ContractStatus.CANCELLED
        await self.repo.update(obj)
        await audit_record(session=self.repo.session, action="cancel", entity_type="purchase_contract", entity_id=obj.id, before=before, after=orm_to_dict(obj))

    async def delete_item(self, item_id: UUID) -> None:
        item = await self.item_repo.get_by_id_or_raise(item_id)
        cid = item.contract_id
        before = orm_to_dict(item)
        await self.item_repo.delete(item)
        await self._recalc_totals(cid)
        await audit_record(session=self.repo.session, action="delete_item", entity_type="purchase_contract", entity_id=cid, before=before, remark=f"删除明细行 {item.line_no}")

    async def _recalc_totals(self, contract_id: UUID) -> None:
        contract = await self.repo.get_with_items(contract_id)
        if contract:
            tq = sum((it.quantity for it in contract.items), Decimal("0"))
            ta = sum((it.amount for it in contract.items), Decimal("0"))
            contract.total_quantity = tq; contract.total_amount = ta
            await self.repo.update(contract)
