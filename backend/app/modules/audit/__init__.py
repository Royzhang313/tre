"""操作审计模块"""

from app.modules import register
from app.modules.audit.router import router

register("audit", router)

__all__: list[str] = []
