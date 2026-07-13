"""系统配置 —— Pydantic Schemas"""

from uuid import UUID

from pydantic import BaseModel, Field


class SysConfigUpdate(BaseModel):
    key: str = Field(min_length=1, max_length=100)
    value: str | None = None
    description: str | None = None


class SysConfigBatchUpdate(BaseModel):
    configs: dict[str, str | None] = Field(description="批量更新配置 {key: value}")


class SysConfigResponse(BaseModel):
    id: UUID; key: str; value: str | None; description: str | None
    model_config = {"from_attributes": True}
