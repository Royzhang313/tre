"""货运模块 —— ORM 数据模型 V2

维度以采购合同为中心，品牌为主筛选轴。
ShippingPlan(品牌→采购合同) → ShippingPlanItem(客户→销售合同→型号/仓库/吨数) → Shipment → ShipmentItem
"""

import enum
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, ForeignKey, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class PlanStatus(enum.StrEnum):
    """计划状态"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    PARTIALLY_SHIPPED = "partially_shipped"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DeliveryMethod(enum.StrEnum):
    """配送方式"""
    PICKUP = "ZT"      # 自提
    DELIVERY = "SH"    # 送货


class SurchargeType(enum.StrEnum):
    """调货类型"""
    BRAND_TRANSFER = "brand_transfer"            # 品牌调货
    CARBONATE_TRANSFER = "carbonate_transfer"    # 碳酸料调货


class ShipmentStatus(enum.StrEnum):
    """发货状态"""
    PENDING = "pending"
    SHIPPED = "shipped"
    RECEIVED = "received"


class ShippingPlan(BaseModel):
    """货运计划（主表）—— 维度：品牌 → 采购合同"""

    __tablename__ = "shipping_plans"

    tenant_id: Mapped[UUID] = mapped_column(nullable=False, default=None)
    company_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_companies.id", ondelete="RESTRICT"), nullable=False, comment="执行主体公司"
    )
    brand_id: Mapped[UUID] = mapped_column(
        ForeignKey("brands.id", ondelete="RESTRICT"), nullable=False, comment="发货品牌（主筛选维度）"
    )
    supplier_enterprise_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), nullable=False, comment="供方企业（筛选采购合同）"
    )
    purchase_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("purchase_contracts.id", ondelete="RESTRICT"), nullable=False, comment="货源采购合同（按品牌筛选）"
    )
    planned_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="计划发货日期(看板维度)")
    delivery_method: Mapped[DeliveryMethod] = mapped_column(
        String(2), nullable=False, default=DeliveryMethod.DELIVERY, comment="配送方式: ZT=自提 SH=送货"
    )
    status: Mapped[PlanStatus] = mapped_column(
        String(20), nullable=False, default=PlanStatus.PENDING
    )
    total_planned_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0")
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True, comment="标签列表")
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False
    )

    items: Mapped[list["ShippingPlanItem"]] = relationship(
        "ShippingPlanItem", back_populates="plan",
        cascade="all, delete-orphan", order_by="ShippingPlanItem.line_no",
    )
    shipments: Mapped[list["Shipment"]] = relationship(
        "Shipment", back_populates="plan",
        cascade="all, delete-orphan", order_by="Shipment.shipped_date",
    )

    def __repr__(self) -> str:
        return f"<ShippingPlan {self.id} date={self.planned_date}>"


class ShippingPlanItem(BaseModel):
    """货运计划明细 —— 客户 → 销售合同 → 型号/仓库/吨数"""

    __tablename__ = "shipping_plan_items"
    __table_args__ = (
        UniqueConstraint("plan_id", "line_no", name="uq_sp_item_line_no"),
    )

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipping_plans.id", ondelete="CASCADE"), nullable=False
    )
    line_no: Mapped[int] = mapped_column(nullable=False)

    # 客户 → 销售合同（按客户筛选）
    customer_enterprise_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="RESTRICT"), nullable=False, comment="客户企业"
    )
    sales_contract_id: Mapped[UUID] = mapped_column(
        ForeignKey("sales_contracts.id", ondelete="RESTRICT"), nullable=False, comment="客户销售合同"
    )

    # 实际发货规格（型号/仓库按计划品牌筛选）
    model_id: Mapped[UUID] = mapped_column(
        ForeignKey("brand_models.id", ondelete="RESTRICT"), nullable=False, comment="发货型号"
    )
    warehouse_id: Mapped[UUID] = mapped_column(
        ForeignKey("brand_warehouses.id", ondelete="RESTRICT"), nullable=False, comment="发货仓库"
    )

    # 数量/价格
    planned_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, comment="计划数量(吨)")
    unit: Mapped[str] = mapped_column(String(10), default="吨", server_default="吨")
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="采购单价")
    sale_price: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="销售单价")

    # 调货
    surcharge_type: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="调货类型")
    surcharge_amount: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="加价单价")

    # 累计已发数量
    shipped_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), default=0, server_default="0", comment="累计已发数量")

    plan: Mapped["ShippingPlan"] = relationship("ShippingPlan", back_populates="items")

    def __repr__(self) -> str:
        return f"<SPI plan={self.plan_id}:{self.line_no}>"


class Shipment(BaseModel):
    """发货记录 —— 每个计划可多次部分发货"""

    __tablename__ = "shipments"

    plan_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipping_plans.id", ondelete="CASCADE"), nullable=False
    )
    shipment_no: Mapped[str] = mapped_column(
        String(30), unique=True, nullable=False, comment="发货编号 FH-{YYYYMMDDhhmmss}"
    )
    shipped_date: Mapped[str] = mapped_column(String(10), nullable=False, comment="实际发货日期")

    driver_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="司机姓名")
    driver_phone: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="司机手机")
    driver_license_plate: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="车牌号")
    driver_id_card: Mapped[str | None] = mapped_column(String(30), nullable=True, comment="司机身份证")

    freight_total: Mapped[Decimal | None] = mapped_column(Numeric(18, 2), nullable=True, comment="运费总额")
    freight_unit_price: Mapped[Decimal | None] = mapped_column(Numeric(18, 4), nullable=True, comment="运费单价")
    freight_tax_rate: Mapped[Decimal | None] = mapped_column(Numeric(5, 2), nullable=True, comment="运费税率")

    status: Mapped[ShipmentStatus] = mapped_column(
        String(20), nullable=False, default=ShipmentStatus.PENDING
    )
    remark: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_by: Mapped[UUID] = mapped_column(
        ForeignKey("auth_users.id", ondelete="RESTRICT"), nullable=False
    )

    plan: Mapped["ShippingPlan"] = relationship("ShippingPlan", back_populates="shipments")
    items: Mapped[list["ShipmentItem"]] = relationship(
        "ShipmentItem", back_populates="shipment",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Shipment {self.shipment_no}>"


class ShipmentItem(BaseModel):
    """发货明细 —— 追踪每行实际发出数量"""

    __tablename__ = "shipment_items"

    shipment_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipments.id", ondelete="CASCADE"), nullable=False
    )
    plan_item_id: Mapped[UUID] = mapped_column(
        ForeignKey("shipping_plan_items.id", ondelete="RESTRICT"), nullable=False, comment="计划明细行"
    )
    shipped_quantity: Mapped[Decimal] = mapped_column(Numeric(18, 4), nullable=False, comment="本次发货数量")
    unit: Mapped[str] = mapped_column(String(10), default="吨", server_default="吨")

    shipment: Mapped["Shipment"] = relationship("Shipment", back_populates="items")
    plan_item: Mapped["ShippingPlanItem"] = relationship("ShippingPlanItem")

    def __repr__(self) -> str:
        return f"<ShipmentItem {self.shipment_id}: {self.shipped_quantity}吨>"
