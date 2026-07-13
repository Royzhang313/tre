"""基础资料模块 —— ORM 模型"""

from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel


class Enterprise(BaseModel):
    """企业"""

    __tablename__ = "basedata_enterprises"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="简称")
    uscc: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="统一社会信用代码")
    enterprise_type: Mapped[list] = mapped_column(JSON, nullable=False, default=list, comment="企业类型多选: trader/factory/end_customer")
    address: Mapped[str | None] = mapped_column(String(300), nullable=True, comment="地址")
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="开户行")
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="对公账户")
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    contacts: Mapped[list["EnterpriseContact"]] = relationship(
        "EnterpriseContact", back_populates="enterprise", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Enterprise {self.name}>"


class EnterpriseContact(BaseModel):
    """企业联系人"""

    __tablename__ = "basedata_enterprise_contacts"

    enterprise_id: Mapped[UUID] = mapped_column(
        ForeignKey("basedata_enterprises.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    mobile: Mapped[str] = mapped_column(String(30), nullable=False)

    enterprise: Mapped["Enterprise"] = relationship("Enterprise", back_populates="contacts")

    def __repr__(self) -> str:
        return f"<Contact {self.name}>"


class Company(BaseModel):
    """执行主体公司"""

    __tablename__ = "basedata_companies"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    short_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    uscc: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(300), nullable=True)
    bank_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    bank_account: Mapped[str | None] = mapped_column(String(50), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<Company {self.name}>"


class Warehouse(BaseModel):
    """仓库"""

    __tablename__ = "basedata_warehouses"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<Warehouse {self.name}>"


class CommissionPlatform(BaseModel):
    """撮合平台"""

    __tablename__ = "basedata_commission_platforms"
    __table_args__ = (UniqueConstraint("name", name="uq_commission_platform_name"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<CommissionPlatform {self.name}>"
