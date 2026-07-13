"""AI Builder —— Pydantic Schemas"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class SpecCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    business_context: str = Field(default="", max_length=500)
    spec_json: dict = Field(default_factory=dict)


class SpecValidateRequest(BaseModel):
    spec_json: dict


class SpecVersionRequest(BaseModel):
    revision_reason: str = Field(min_length=1, max_length=500)


class SpecApproveRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)


class SpecResponse(BaseModel):
    id: UUID
    version: str
    title: str
    business_context: str
    status: str
    spec_json: dict | None
    impact_analysis: str | None
    risks: str | None
    reviewed_by: UUID | None
    reviewed_at: str | None
    review_comment: str | None
    created_at: datetime
    updated_at: datetime
    model_config = {"from_attributes": True}
