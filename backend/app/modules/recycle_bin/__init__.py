"""回收站模块"""

from app.modules import register
from app.modules.recycle_bin.router import router

register("recycle_bin", router)

__all__: list[str] = []
