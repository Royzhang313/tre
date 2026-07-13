"""品牌模块 —— PET 品牌 + 发货仓库 + 型号"""

from app.modules import register
from app.modules.brand.router import router

register("brand", router)

__all__: list[str] = []
