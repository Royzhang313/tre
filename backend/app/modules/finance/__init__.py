"""财务模块"""
from app.modules import register
from app.modules.finance.router import router

register("finance", router)
