"""Product 产品模块（MVP 简化版）

产品模块提供独立的产品实体，用于 MVP 阶段快速验证。
后续可演进为 Brand + BrandModel 体系。
"""

from app.modules import register
from .router import router

register("product", router)
