"""系统配置 —— ORM 模型"""

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.shared.base_model import BaseModel


class SysConfig(BaseModel):
    """系统配置键值存储"""

    __tablename__ = "sys_configs"

    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, comment="配置键")
    value: Mapped[str | None] = mapped_column(String(5000), nullable=True, comment="配置值（JSON 字符串）")
    description: Mapped[str | None] = mapped_column(String(500), nullable=True, comment="配置说明")
