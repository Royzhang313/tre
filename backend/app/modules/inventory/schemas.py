"""库存统计 —— 只读聚合视图，无独立模型"""
from uuid import UUID

from pydantic import BaseModel


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
    shipped_this_quarter: float
    shipped_this_year: float
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
