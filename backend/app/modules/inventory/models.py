"""库存模块 —— ORM 数据模型

核心创新：合同货权库存（ContractStock）。
- 合同生效即产生货权（qty_in_transit）
- 收货入库后转为在仓（qty_in_warehouse）
- 销售锁货（qty_allocated）
- 发运交付（qty_shipped）

双层库存模型：
  ContractStock（货权层）—— "我买了多少、还有多少可卖"
  WarehouseStock（实物层）—— "仓库里实际有多少"
"""

from decimal import Decimal
from uuid import UUID

from sqlalchemy import ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class ContractStock(BaseModel):
    """合同货权库存 —— 每个采购合同的每个产品一条记录

    可用数量公式：available = qty_in_warehouse - qty_allocated

    数量状态推导（不存 status 字段）：
      in_transit:      qty_in_transit > 0, qty_in_warehouse == 0, qty_shipped == 0
      in_warehouse:    qty_in_warehouse > 0, qty_shipped == 0
      partial_shipped: qty_shipped > 0, qty_shipped < qty_contracted
      complete:        qty_shipped == qty_contracted
    """

    __tablename__ = "contract_stocks"
    __table_args__ = (
        UniqueConstraint("product_id", "purchase_contract_id", name="uq_cs_product_po"),
    )

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, comment="产品"
    )
    purchase_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_contracts.id", ondelete="RESTRICT"),
        nullable=False,
        comment="采购合同",
    )
    supplier_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"),
        nullable=False,
        comment="供应商",
    )

    # ---- 数量字段（吨，Decimal(18,4)） ----
    qty_contracted: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="合同总量"
    )
    qty_in_transit: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="在途量（合同生效-未入库）"
    )
    qty_in_warehouse: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="在仓量（已入库可用）"
    )
    qty_allocated: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="已分配量（锁给客户）"
    )
    qty_shipped: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="已发运量（已交付客户）"
    )

    is_closed: Mapped[bool] = mapped_column(default=False, server_default="false", comment="手动关结标志")

    def __repr__(self) -> str:
        return f"<ContractStock product={self.product_id} po={self.purchase_contract_id}>"

    @property
    def qty_available(self) -> Decimal:
        """可售数量 = 在仓 - 已分配"""
        return self.qty_in_warehouse - self.qty_allocated

    @property
    def status_label(self) -> str:
        """推导状态标签"""
        if self.qty_shipped == self.qty_contracted and self.qty_contracted > 0:
            return "complete"
        if self.qty_shipped > 0:
            return "partial_shipped"
        if self.qty_in_warehouse > 0:
            return "in_warehouse"
        if self.qty_in_transit > 0:
            return "in_transit"
        return "pending"


class WarehouseStock(BaseModel):
    """实物库存 —— 仓库中实际存在的货物

    与 ContractStock（货权层）互补：
    - ContractStock 回答"我有多少货权"
    - WarehouseStock 回答"仓库里实际有多少"
    """

    __tablename__ = "warehouse_stocks"
    __table_args__ = (
        UniqueConstraint("warehouse_id", "product_id", name="uq_ws_warehouse_product"),
    )

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_warehouses.id", ondelete="RESTRICT"), nullable=False, comment="仓库"
    )
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, comment="产品"
    )
    qty_on_hand: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, server_default="0", comment="现有实物数量(吨)"
    )

    def __repr__(self) -> str:
        return f"<WarehouseStock wh={self.warehouse_id} product={self.product_id} qty={self.qty_on_hand}>"


class Batch(BaseModel):
    """批次 —— 成本核算单元

    每个批次关联一个采购合同，记录来源单价。
    同一产品不同批次可有不同成本（不同供应商、不同采购时间）。
    出库成本按批次实际采购价计算，而非移动平均。
    """

    __tablename__ = "batches"

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    product_id: Mapped[UUID] = mapped_column(
        ForeignKey("products.id", ondelete="RESTRICT"), nullable=False, comment="产品"
    )
    purchase_contract_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("purchase_contracts.id", ondelete="SET NULL"), nullable=True, comment="采购合同"
    )
    warehouse_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("basedata_warehouses.id", ondelete="SET NULL"), nullable=True, comment="仓库"
    )
    batch_number: Mapped[str] = mapped_column(
        String(100), nullable=False, comment="批次号"
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, comment="批次数量(吨)"
    )
    cost_price: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, default=0, comment="成本单价"
    )
    receipt_date: Mapped[str | None] = mapped_column(
        String(10), nullable=True, comment="入库日期"
    )
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true", comment="是否有效")

    def __repr__(self) -> str:
        return f"<Batch {self.batch_number} product={self.product_id}>"


class InventoryLedger(BaseModel):
    """库存分类账 —— 记录每次库存变动

    账户体系：
      IN_TRANSIT   - 在途库存（已采购未入库）
      IN_WAREHOUSE - 在仓库存（已入库可用）
      ALLOCATED    - 已分配库存（承诺给客户，锁货）
      COMMITTED    - 已承诺库存（已承诺未发运）
      DELIVERED    - 已交付（已发运给客户）
    """

    __tablename__ = "inventory_ledger"

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    contract_stock_id: Mapped[UUID] = mapped_column(
        ForeignKey("contract_stocks.id", ondelete="RESTRICT"), nullable=False, comment="关联货权库存"
    )
    account_code: Mapped[str] = mapped_column(
        String(20), nullable=False, comment="账户代码: IN_TRANSIT/IN_WAREHOUSE/ALLOCATED/COMMITTED/DELIVERED"
    )
    change_qty: Mapped[Decimal] = mapped_column(
        Numeric(18, 4), nullable=False, comment="变动数量（正=增加，负=减少）"
    )
    event_type: Mapped[str | None] = mapped_column(
        String(50), nullable=True, comment="事件类型"
    )
    reference_id: Mapped[UUID | None] = mapped_column(nullable=True, comment="关联单据ID")
    remark: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="备注")

    def __repr__(self) -> str:
        return f"<InventoryLedger {self.account_code} {self.change_qty}>"
