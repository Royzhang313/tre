"""库存模块 —— Pydantic Schemas

包含：
- 品牌维度库存聚合视图（过渡方案）
- ContractStock 请求/响应 Schema
- WarehouseStock Schema
- Batch Schema
- InventoryLedger Schema
- 库存操作请求
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, Field


# ============================================================
# 品牌维度库存聚合视图（过渡方案）
# ============================================================


class InventoryByBrand(BaseModel):
    """品牌维度库存"""
    brand_id: UUID
    brand_name: str
    brand_color: str
    purchased_qty: float           # 采购合同总量
    sold_qty: float                 # 销售合同总量
    shipped_qty: float              # 实际发货总量（累计）
    shipped_this_month: float       # 本月发货
    shipped_last_month: float       # 上月发货
    shipped_this_quarter: float     # 本季度发货
    shipped_this_year: float        # 本年度发货
    stock_after_sale: float         # 销售后库存 = 采购 - 销售
    stock_after_ship: float         # 发货后库存 = 采购 - 发货


class InventoryStatsResponse(BaseModel):
    items: list[InventoryByBrand]
    total_purchased: float
    total_sold: float
    total_shipped: float
    total_stock_after_sale: float
    total_stock_after_ship: float


class InventoryByWarehouse(BaseModel):
    """品牌+仓库维度库存"""
    brand_id: UUID
    brand_name: str
    brand_color: str
    warehouse_id: UUID
    warehouse_name: str
    purchased_qty: float
    sold_qty: float
    shipped_qty: float
    shipped_this_month: float
    shipped_last_month: float
    shipped_this_quarter: float
    shipped_this_year: float
    stock_after_sale: float
    stock_after_ship: float


class InventoryWarehouseStatsResponse(BaseModel):
    items: list[InventoryByWarehouse]
    total_purchased: float
    total_sold: float
    total_shipped: float
    total_stock_after_sale: float
    total_stock_after_ship: float


# ============================================================
# ContractStock（合同货权库存）
# ============================================================


class ContractStockCreate(BaseModel):
    """创建货权库存记录"""
    product_id: UUID = Field(description="产品ID")
    purchase_contract_id: UUID = Field(description="采购合同ID")
    supplier_id: UUID = Field(description="供应商ID")
    qty_contracted: Decimal = Field(default=Decimal("0"), max_digits=18, decimal_places=4, description="合同总量(吨)")


class ContractStockUpdate(BaseModel):
    """更新货权库存"""
    qty_in_transit: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="在途量")
    qty_in_warehouse: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="在仓量")
    qty_allocated: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="已分配量")
    qty_shipped: Decimal | None = Field(None, max_digits=18, decimal_places=4, description="已发运量")
    is_closed: bool | None = Field(None, description="手动关结")


class ContractStockResponse(BaseModel):
    """货权库存响应"""
    id: UUID
    product_id: UUID
    purchase_contract_id: UUID
    supplier_id: UUID
    qty_contracted: Decimal
    qty_in_transit: Decimal
    qty_in_warehouse: Decimal
    qty_allocated: Decimal
    qty_shipped: Decimal
    qty_available: float = Field(default=0, description="可售数量 = 在仓 - 已分配")
    status_label: str = Field(default="pending", description="状态标签")
    is_closed: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# WarehouseStock（实物库存）
# ============================================================


class WarehouseStockResponse(BaseModel):
    """实物库存响应"""
    id: UUID
    warehouse_id: UUID
    product_id: UUID
    qty_on_hand: Decimal
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# Batch（批次）
# ============================================================


class BatchCreate(BaseModel):
    """创建批次"""
    product_id: UUID
    purchase_contract_id: UUID | None = None
    warehouse_id: UUID | None = None
    batch_number: str = Field(min_length=1, max_length=100, description="批次号")
    quantity: Decimal = Field(gt=0, max_digits=18, decimal_places=4, description="批次数量(吨)")
    cost_price: Decimal = Field(ge=0, max_digits=18, decimal_places=4, description="成本单价")
    receipt_date: str | None = Field(None, max_length=10, description="入库日期")


class BatchUpdate(BaseModel):
    """更新批次"""
    batch_number: str | None = Field(None, max_length=100)
    quantity: Decimal | None = Field(None, max_digits=18, decimal_places=4)
    cost_price: Decimal | None = Field(None, max_digits=18, decimal_places=4)
    receipt_date: str | None = Field(None, max_length=10)
    is_active: bool | None = None


class BatchResponse(BaseModel):
    """批次响应"""
    id: UUID
    product_id: UUID
    purchase_contract_id: UUID | None
    warehouse_id: UUID | None
    batch_number: str
    quantity: Decimal
    cost_price: Decimal
    receipt_date: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# InventoryLedger（库存分类账）
# ============================================================


class InventoryLedgerResponse(BaseModel):
    """库存分类账响应"""
    id: UUID
    contract_stock_id: UUID
    account_code: str
    change_qty: Decimal
    event_type: str | None
    reference_id: UUID | None
    remark: str | None
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# 库存操作请求
# ============================================================


class StockReceiptRequest(BaseModel):
    """收货入库请求 —— 在途 → 在仓"""
    contract_stock_id: UUID
    receipt_qty: Decimal = Field(gt=0, max_digits=18, decimal_places=4, description="入库数量(吨)")
    warehouse_id: UUID = Field(description="入库仓库")


class StockAllocationRequest(BaseModel):
    """锁货请求 —— 为销售合同分配库存"""
    contract_stock_id: UUID
    sales_contract_id: UUID = Field(description="销售合同ID")
    allocate_qty: Decimal = Field(gt=0, max_digits=18, decimal_places=4, description="分配数量(吨)")


class StockDeliveryRequest(BaseModel):
    """出库交付请求 —— 已分配 → 已发运"""
    contract_stock_id: UUID
    deliver_qty: Decimal = Field(gt=0, max_digits=18, decimal_places=4, description="交付数量(吨)")


# ============================================================
# 列表响应
# ============================================================


class ContractStockListResponse(BaseModel):
    """货权库存列表响应"""
    items: list[ContractStockResponse]
    total: int
