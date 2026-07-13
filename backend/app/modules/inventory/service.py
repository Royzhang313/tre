"""库存模块 —— Service 层

核心业务逻辑：
- 合同确认 → ContractStock 产生（qty_in_transit += qty）
- 收货入库 → 在途转在仓（qty_in_transit -= qty, qty_in_warehouse += qty）
- 销售锁货 → 已分配（qty_allocated += qty）
- 发运交付 → 已发运（qty_allocated -= qty, qty_shipped += qty）
"""

from decimal import Decimal
from uuid import UUID

from app.core.exceptions import BusinessRuleViolationError, ConflictError, NotFoundError
from app.modules.inventory.models import (
    Batch,
    ContractStock,
    InventoryLedger,
    WarehouseStock,
)
from app.modules.inventory.repository import (
    BatchRepository,
    ContractStockRepository,
    InventoryLedgerRepository,
    WarehouseStockRepository,
)
from app.shared.audit_helper import audit_record, orm_to_dict

# 确保 FK 引用表已注册到 SQLAlchemy metadata
import app.modules.product.models  # noqa: F401  (products)
import app.modules.purchase_contract.models  # noqa: F401  (purchase_contracts)
import app.modules.basedata.models  # noqa: F401  (basedata_enterprises, basedata_warehouses)


class ContractStockService:
    """合同货权库存服务"""

    def __init__(
        self,
        repo: ContractStockRepository,
        ledger_repo: InventoryLedgerRepository,
        wh_stock_repo: WarehouseStockRepository,
        batch_repo: BatchRepository,
    ):
        self.repo = repo
        self.ledger_repo = ledger_repo
        self.wh_stock_repo = wh_stock_repo
        self.batch_repo = batch_repo

    # ============================================================
    # 库存初始化（合同确认时调用）
    # ============================================================

    async def create_from_contract(
        self,
        product_id: UUID,
        purchase_contract_id: UUID,
        supplier_id: UUID,
        tenant_id: UUID,
        qty_contracted: Decimal,
    ) -> ContractStock:
        """合同确认后创建货权库存 —— 全部记为在途"""
        existing = await self.repo.get_by_product_and_po(product_id, purchase_contract_id)
        if existing:
            raise ConflictError(
                f"产品 {product_id} 在合同 {purchase_contract_id} 下已有货权记录",
                entity="ContractStock",
            )

        stock = ContractStock(
            tenant_id=tenant_id,
            product_id=product_id,
            purchase_contract_id=purchase_contract_id,
            supplier_id=supplier_id,
            qty_contracted=qty_contracted,
            qty_in_transit=qty_contracted,  # 合同确认后全部为在途
            qty_in_warehouse=Decimal("0"),
            qty_allocated=Decimal("0"),
            qty_shipped=Decimal("0"),
        )
        await self.repo.create(stock)

        # 记录分类账
        await self._write_ledger(
            stock.id,
            tenant_id,
            "IN_TRANSIT",
            qty_contracted,
            "purchase.order.confirmed",
            purchase_contract_id,
            "采购合同确认，货权产生",
        )

        await audit_record(
            session=self.repo.session,
            action="create",
            entity_type="contract_stock",
            entity_id=stock.id,
            after=orm_to_dict(stock),
        )
        return stock

    # ============================================================
    # 收货入库：在途 → 在仓
    # ============================================================

    async def receipt(
        self,
        contract_stock_id: UUID,
        receipt_qty: Decimal,
        warehouse_id: UUID,
        tenant_id: UUID,
    ) -> ContractStock:
        """收货入库 —— 在途减少，在仓增加"""
        stock = await self.repo.get_by_id_or_raise(contract_stock_id)

        if stock.qty_in_transit < receipt_qty:
            raise BusinessRuleViolationError(
                f"在途库存不足：需要 {receipt_qty}t，在途仅 {stock.qty_in_transit}t",
                rule="INSUFFICIENT_IN_TRANSIT",
            )

        stock.qty_in_transit -= receipt_qty
        stock.qty_in_warehouse += receipt_qty
        await self.repo.update(stock)

        # 记录分类账
        await self._write_ledger(
            stock.id, tenant_id, "IN_TRANSIT", -receipt_qty,
            "purchase.receipt.confirmed", contract_stock_id, "收货入库-在途减少",
        )
        await self._write_ledger(
            stock.id, tenant_id, "IN_WAREHOUSE", receipt_qty,
            "purchase.receipt.confirmed", contract_stock_id, "收货入库-在仓增加",
        )

        # 更新实物库存
        await self._upsert_warehouse_stock(
            warehouse_id, stock.product_id, receipt_qty, tenant_id
        )

        await audit_record(
            session=self.repo.session,
            action="receipt",
            entity_type="contract_stock",
            entity_id=stock.id,
            after=orm_to_dict(stock),
            remark=f"入库 {receipt_qty}t → 仓库 {warehouse_id}",
        )
        return stock

    # ============================================================
    # 销售锁货：已分配
    # ============================================================

    async def allocate(
        self,
        contract_stock_id: UUID,
        allocate_qty: Decimal,
        tenant_id: UUID,
        sales_contract_id: UUID | None = None,
    ) -> ContractStock:
        """为销售合同锁货 —— 增加已分配量"""
        stock = await self.repo.get_by_id_or_raise(contract_stock_id)

        available = stock.qty_in_warehouse - stock.qty_allocated
        if available < allocate_qty:
            raise BusinessRuleViolationError(
                f"可用库存不足：需要 {allocate_qty}t，可用仅 {available}t",
                rule="INSUFFICIENT_AVAILABLE",
            )

        stock.qty_allocated += allocate_qty
        await self.repo.update(stock)

        await self._write_ledger(
            stock.id, tenant_id, "ALLOCATED", allocate_qty,
            "sales.contract.confirmed", sales_contract_id,
            f"销售合同锁货 {allocate_qty}t",
        )

        await audit_record(
            session=self.repo.session,
            action="allocate",
            entity_type="contract_stock",
            entity_id=stock.id,
            after=orm_to_dict(stock),
            remark=f"锁货 {allocate_qty}t → 销售合同 {sales_contract_id}",
        )
        return stock

    # ============================================================
    # 发运交付：已分配 → 已发运
    # ============================================================

    async def deliver(
        self,
        contract_stock_id: UUID,
        deliver_qty: Decimal,
        tenant_id: UUID,
        warehouse_id: UUID | None = None,
    ) -> ContractStock:
        """发运交付 —— 已分配减少，已发运增加"""
        stock = await self.repo.get_by_id_or_raise(contract_stock_id)

        if stock.qty_allocated < deliver_qty:
            raise BusinessRuleViolationError(
                f"已分配库存不足：需要 {deliver_qty}t，已分配仅 {stock.qty_allocated}t",
                rule="INSUFFICIENT_ALLOCATED",
            )

        stock.qty_allocated -= deliver_qty
        stock.qty_shipped += deliver_qty
        await self.repo.update(stock)

        await self._write_ledger(
            stock.id, tenant_id, "ALLOCATED", -deliver_qty,
            "inventory.delivered", contract_stock_id, "发运交付-释放锁货",
        )
        await self._write_ledger(
            stock.id, tenant_id, "DELIVERED", deliver_qty,
            "inventory.delivered", contract_stock_id, "发运交付-已交付",
        )

        # 减少实物库存
        if warehouse_id:
            await self._upsert_warehouse_stock(
                warehouse_id, stock.product_id, -deliver_qty, tenant_id
            )

        await audit_record(
            session=self.repo.session,
            action="deliver",
            entity_type="contract_stock",
            entity_id=stock.id,
            after=orm_to_dict(stock),
            remark=f"发运交付 {deliver_qty}t",
        )
        return stock

    # ============================================================
    # 内部辅助方法
    # ============================================================

    async def _write_ledger(
        self,
        contract_stock_id: UUID,
        tenant_id: UUID,
        account_code: str,
        change_qty: Decimal,
        event_type: str | None,
        reference_id: UUID | None,
        remark: str | None,
    ) -> None:
        """写入库存分类账"""
        ledger = InventoryLedger(
            tenant_id=tenant_id,
            contract_stock_id=contract_stock_id,
            account_code=account_code,
            change_qty=change_qty,
            event_type=event_type,
            reference_id=reference_id,
            remark=remark,
        )
        await self.ledger_repo.create(ledger)

    async def _upsert_warehouse_stock(
        self,
        warehouse_id: UUID,
        product_id: UUID,
        qty_delta: Decimal,
        tenant_id: UUID,
    ) -> None:
        """更新或创建实物库存"""
        existing = await self.wh_stock_repo.get_by_warehouse_and_product(
            warehouse_id, product_id
        )
        if existing:
            existing.qty_on_hand += qty_delta
            await self.wh_stock_repo.update(existing)
        else:
            ws = WarehouseStock(
                tenant_id=tenant_id,
                warehouse_id=warehouse_id,
                product_id=product_id,
                qty_on_hand=qty_delta,
            )
            await self.wh_stock_repo.create(ws)


class BatchService:
    """批次服务"""

    def __init__(self, repo: BatchRepository):
        self.repo = repo

    async def create_batch(
        self, product_id: UUID, batch_number: str, quantity: Decimal,
        cost_price: Decimal, purchase_contract_id: UUID | None = None,
        warehouse_id: UUID | None = None, receipt_date: str | None = None,
        tenant_id: UUID | None = None,
    ) -> Batch:
        """创建批次"""
        batch = Batch(
            tenant_id=tenant_id or UUID("00000000-0000-0000-0000-000000000000"),
            product_id=product_id,
            purchase_contract_id=purchase_contract_id,
            warehouse_id=warehouse_id,
            batch_number=batch_number,
            quantity=quantity,
            cost_price=cost_price,
            receipt_date=receipt_date,
        )
        await self.repo.create(batch)
        await audit_record(
            session=self.repo.session,
            action="create",
            entity_type="batch",
            entity_id=batch.id,
            after=orm_to_dict(batch),
        )
        return batch
