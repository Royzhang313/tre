"""库存模块

包含：
- ContractStock（合同货权库存）
- WarehouseStock（实物库存）
- Batch（批次）
- InventoryLedger（库存分类账）
- 品牌维度库存统计（过渡聚合视图）
"""

# 确保 ORM 模型在模块导入时注册到 SQLAlchemy Base.metadata
from app.modules.inventory import models  # noqa: F401

from app.modules import register
from .router import router

register("inventory", router)
