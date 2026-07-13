"""品牌模块 —— Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class BrandCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    color: str = Field(min_length=1, max_length=20)


class BrandUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    color: str | None = Field(default=None, max_length=20)
    sort_order: int | None = None
    is_active: bool | None = None


class BrandReorderItem(BaseModel):
    id: UUID
    sort_order: int


class BrandReorderRequest(BaseModel):
    items: list[BrandReorderItem]


class BrandResponse(BaseModel):
    id: UUID; name: str; color: str; sort_order: int; is_active: bool
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class BrandFullResponse(BaseModel):
    id: UUID; name: str; color: str; sort_order: int; is_active: bool
    warehouses: list["BrandWarehouseResponse"] = []
    models: list["BrandModelResponse"] = []
    created_at: datetime; updated_at: datetime
    model_config = {"from_attributes": True}


class BrandWarehouseCreate(BaseModel):
    brand_id: UUID
    name: str = Field(min_length=1, max_length=100)


class BrandWarehouseResponse(BaseModel):
    id: UUID; brand_id: UUID; name: str; sort_order: int; is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BrandWarehouseReorderItem(BaseModel):
    id: UUID
    sort_order: int


class BrandWarehouseReorderRequest(BaseModel):
    brand_id: UUID
    items: list[BrandWarehouseReorderItem]


class BrandModelCreate(BaseModel):
    brand_id: UUID
    model_name: str = Field(min_length=1, max_length=100)
    model_type: str = Field(default="热料")


class BrandModelResponse(BaseModel):
    id: UUID; brand_id: UUID; model_name: str; model_type: str; sort_order: int; is_active: bool
    created_at: datetime
    model_config = {"from_attributes": True}


class BrandModelReorderItem(BaseModel):
    id: UUID
    sort_order: int


class BrandModelReorderRequest(BaseModel):
    brand_id: UUID
    items: list[BrandModelReorderItem]
