"""销售合同模块"""

from app.modules import register
from app.modules.sales_contract.router import router

register("sales_contract", router)

__all__: list[str] = []
