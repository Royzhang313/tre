"""基础资料模块 —— ORM 模型（SaaS 多租户版）

所有业务实体均包含 tenant_id 实现行级数据隔离。
"""

from uuid import UUID

from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.shared.base_model import BaseModel
from app.shared.tenant import TenantMixin


class Enterprise(BaseModel, TenantMixin):
    """企业（外部商业实体 —— 客户 / 供应商 / 贸易商 / 工厂）

    统一管理所有外部商业伙伴。通过 enterprise_type JSON 字段多选标记角色，
    同一企业可同时作为客户和供应商。
    """

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


class EnterpriseContact(BaseModel, TenantMixin):
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


class Company(BaseModel, TenantMixin):
    """执行主体公司（我方内部法律实体）

    采购合同和销售合同均绑定 company_id，决定以哪家主体公司签约。
    在财务模块（收款/付款）中作为收款方/付款方。
    """

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


class Warehouse(BaseModel, TenantMixin):
    """仓库（物理仓库）"""

    __tablename__ = "basedata_warehouses"

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<Warehouse {self.name}>"


class CommissionPlatform(BaseModel, TenantMixin):
    """撮合平台"""

    __tablename__ = "basedata_commission_platforms"
    __table_args__ = (UniqueConstraint("name", name="uq_commission_platform_name"),)

    name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True, server_default="true")

    def __repr__(self) -> str:
        return f"<CommissionPlatform {self.name}>"
