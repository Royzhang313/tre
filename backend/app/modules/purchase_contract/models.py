"""采购合同模块 —— ORM 数据模型 V2

采购合同主表 + 明细表。
明细引用品牌/品牌型号/发货仓库。
"""

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class ContractStatus(enum.StrEnum):
    PENDING = "pending_execution"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PurchaseContract(BaseModel):
    """采购合同（主表）"""

    __tablename__ = "purchase_contracts"

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_companies.id", ondelete="RESTRICT"), nullable=False, comment="执行主体公司"
    )
    contract_no: Mapped[str] = mapped_column(String(30), unique=True, nullable=False, comment="合同编号（手动输入）")
    supplier_enterprise_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), nullable=False
    )
    contract_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="合同签订日期")
    contract_start_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="合同开始日期")
    contract_end_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="合同结束日期")
    attachment_path: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="合同附件列表 [{path, filename}]")
    status: Mapped[ContractStatus] = mapped_column(
        String(20), nullable=False, default=ContractStatus.PENDING
    )
    total_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0")
    total_amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0")
    delivery_progress: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, server_default="0")
    payment_progress: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, server_default="0")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="标签列表，自由添加")
    commission_platform_id: Mapped[UUID | None] = mapped_column(nullable=True, comment="撮合平台")
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False
    )

    items: Mapped[list["PurchaseContractItem"]] = relationship(
        "PurchaseContractItem", back_populates="contract",
        cascade="all, delete-orphan", order_by="PurchaseContractItem.line_no",
    )

    def __repr__(self) -> str:
        return f"<PurchaseContract {self.contract_no}>"


class PurchaseContractItem(BaseModel):
    """采购合同明细"""

    __tablename__ = "purchase_contract_items"
    __table_args__ = (
        UniqueConstraint("contract_id", "line_no", name="uq_pc_item_line_no"),
    )

    contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_contracts.id", ondelete="CASCADE"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(nullable=False)

    # 品牌 / 型号 / 发货仓库（引用品牌模块）
    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, comment="PET品牌"
    )
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("brand_models.id", ondelete="RESTRICT"), nullable=False, comment="品牌型号"
    )
    shipping_warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("brand_warehouses.id", ondelete="RESTRICT"), nullable=False, comment="品牌发货仓库"
    )

    # 数量/价格
    quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, comment="数量(吨)")
    unit: Mapped[str] = mapped_column(String(10), default="吨", server_default="吨")
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False)
    amount: Mapped[Decimal] = mapped_column(Numeric(18, 2), nullable=False)
    tax_rate: Mapped[Decimal] = mapped_column(Numeric(5, 2), default=0, server_default="0")

    # 费用明细
    storage_fee_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0")
    commission_fee_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0")
    commission_fee: Mapped[Decimal] = mapped_column(Numeric(18, 2), default=0, server_default="0")

    contract: Mapped["PurchaseContract"] = relationship("PurchaseContract", back_populates="items")

    def __repr__(self) -> str:
        return f"<PCI {self.contract_id}:{self.line_no}>"
