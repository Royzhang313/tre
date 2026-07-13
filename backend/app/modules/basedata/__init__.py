"""基础资料模块 —— Enterprise / Product / Warehouse"""

from app.modules import register
from app.modules.basedata.router import router

register("basedata", router)

__all__: list[str] = []
