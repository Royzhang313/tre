"""采购合同模块"""

from app.modules import register
from app.modules.purchase_contract.router import router

register("purchase_contract", router)

__all__: list[str] = []
