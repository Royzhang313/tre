"""基础资料 —— Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class EnterpriseContactCreate(BaseModel):
    name: str = Field(min_length=1, max_length=50)
    mobile: str = Field(min_length=1, max_length=30)


class EnterpriseContactResponse(BaseModel):
    id: UUID; name: str; mobile: str
    model_config = {"from_attributes": True}


class EnterpriseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    short_name: str | None = Field(default=None, max_length=50)
    uscc: str | None = Field(default=None, max_length=50)
    enterprise_type: list[str] = Field(default_factory=lambda: ["trader"])
    address: str | None = Field(default=None, max_length=300)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account: str | None = Field(default=None, max_length=50)
    contacts: list[EnterpriseContactCreate] = Field(default_factory=list)


class EnterpriseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    short_name: str | None = Field(default=None, max_length=50)
    uscc: str | None = Field(default=None, max_length=50)
    enterprise_type: list[str] | None = None
    address: str | None = Field(default=None, max_length=300)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account: str | None = Field(default=None, max_length=50)
    is_active: bool | None = None


class EnterpriseResponse(BaseModel):
    id: UUID; name: str; short_name: str | None; uscc: str | None
    enterprise_type: list; address: str | None; bank_name: str | None; bank_account: str | None
    is_active: bool; created_at: datetime; updated_at: datetime
    contacts: list[EnterpriseContactResponse] = []
    model_config = {"from_attributes": True}


class CompanyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    short_name: str | None = Field(default=None, max_length=50)
    uscc: str | None = Field(default=None, max_length=50)
    address: str | None = Field(default=None, max_length=300)
    bank_name: str | None = Field(default=None, max_length=100)
    bank_account: str | None = Field(default=None, max_length=50)


class CompanyUpdate(BaseModel):
    name: str | None = None; short_name: str | None = None; uscc: str | None = None
    address: str | None = None; bank_name: str | None = None; bank_account: str | None = None
    is_active: bool | None = None


class CompanyResponse(BaseModel):
    id: UUID; name: str; short_name: str | None; uscc: str | None
    address: str | None; bank_name: str | None; bank_account: str | None
    is_active: bool; created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class WarehouseCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class WarehouseUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class WarehouseResponse(BaseModel):
    id: UUID; name: str; is_active: bool
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


# ---- 撮合平台 ----

class CommissionPlatformCreate(BaseModel):
    name: str = Field(min_length=1, max_length=200)


class CommissionPlatformUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    is_active: bool | None = None


class CommissionPlatformResponse(BaseModel):
    id: UUID; name: str; is_active: bool
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}
