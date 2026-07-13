"""共享内核（DDD Shared Kernel）—— 稳定公共接口

导出原则：
- 只导出 Base / Protocol / Dataclass / 稳定公共接口
- Protocol 和内部实现请按模块引用（例如 from app.shared.workflow import WorkflowRegistry）
"""

# Model
# Attachment
from app.shared.attachment import AttachmentMeta, AttachmentStorage

# Audit
from app.shared.audit import AuditLogWriter, AuditOperator
from app.shared.base_model import (
    BaseModel,
    SoftDeleteMixin,
    TimestampMixin,
    UUIDPrimaryKey,
    VersionMixin,
)

# Repository
from app.shared.base_repository import BaseRepository

# Schema
from app.shared.base_schema import APIResponse, FilterSchema, PageRequest, PageResponse, SortSchema

# Service
from app.shared.base_service import BaseService

# Pagination
from app.shared.pagination import PageParams, paginate

# Serial Number
from app.shared.serial_number import SerialNumberGenerator

# Workflow
from app.shared.workflow import (
    WorkflowDefinition,
    WorkflowRegistry,
    WorkflowState,
    WorkflowTransition,
)
from app.shared.workflow.exceptions import (
    InvalidTransitionError,
    WorkflowError,
    WorkflowStateNotFoundError,
)

__all__ = [
    # Model
    "BaseModel",
    "UUIDPrimaryKey",
    "TimestampMixin",
    "SoftDeleteMixin",
    "VersionMixin",
    # Repository
    "BaseRepository",
    # Schema
    "APIResponse",
    "PageRequest",
    "PageResponse",
    "FilterSchema",
    "SortSchema",
    # Service
    "BaseService",
    # Pagination
    "PageParams",
    "paginate",
    # Workflow
    "WorkflowState",
    "WorkflowTransition",
    "WorkflowDefinition",
    "WorkflowRegistry",
    "WorkflowError",
    "InvalidTransitionError",
    "WorkflowStateNotFoundError",
    # Audit
    "AuditOperator",
    "AuditLogWriter",
    # Attachment
    "AttachmentMeta",
    "AttachmentStorage",
    # Serial Number
    "SerialNumberGenerator",
]
