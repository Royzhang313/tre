"""系统配置模块"""
from app.modules import register
from app.modules.system.router import router

register("system", router)
