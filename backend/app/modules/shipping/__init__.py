from app.modules import register
from app.modules.shipping.router import router

register("shipping", router)
