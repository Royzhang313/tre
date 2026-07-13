"""Auth 模块 —— Pydantic Schemas（DTO / API 边界）

统一使用 app.shared.base_schema.APIResponse 作为响应包装。
列表接口使用 PageResponse[T] 分页。
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.modules.auth.models import UserStatus

# ============================================================
# 用户
# ============================================================


class UserCreate(BaseModel):
    """创建用户请求"""

    username: str = Field(min_length=2, max_length=50, description="登录名")
    phone: str | None = Field(default=None, max_length=20, description="手机号，可用于登录")
    email: str | None = Field(default=None, max_length=255, description="邮箱")
    password: str = Field(min_length=8, max_length=128, description="明文密码，Service 层做 bcrypt 哈希")
    display_name: str = Field(min_length=1, max_length=100, description="显示名")
    role_ids: list[UUID] | None = Field(default=None, description="初始角色 ID 列表")


class UserUpdate(BaseModel):
    """更新用户资料 —— 所有字段可选"""

    phone: str | None = Field(default=None, max_length=20)
    email: str | None = Field(default=None, max_length=255)
    display_name: str | None = Field(default=None, min_length=1, max_length=100)


class UserStatusUpdate(BaseModel):
    """更新用户状态 —— status 为独立操作，不与资料修改混在一起"""

    status: UserStatus


class UserResponse(BaseModel):
    """用户响应"""

    id: UUID
    username: str
    phone: str | None = None
    email: str | None = None
    display_name: str
    status: UserStatus
    last_login_at: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# 角色
# ============================================================


class RoleCreate(BaseModel):
    """创建角色请求"""

    code: str = Field(min_length=2, max_length=50, description="角色编码")
    name: str = Field(min_length=1, max_length=100, description="角色名称")
    description: str | None = Field(default=None, max_length=255)


class RoleUpdate(BaseModel):
    """更新角色请求"""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=255)


class RoleResponse(BaseModel):
    """角色响应"""

    id: UUID
    code: str
    name: str
    description: str | None
    is_system: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# 权限
# ============================================================


class PermissionResponse(BaseModel):
    """权限响应"""

    id: UUID
    code: str
    name: str
    module: str
    resource: str
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}


# ============================================================
# 认证
# ============================================================


class LoginRequest(BaseModel):
    """登录请求"""

    username: str = Field(min_length=1, description="用户名")
    password: str = Field(min_length=1, description="明文密码（登录不限制长度，兼容旧密码）")


class LoginResponse(BaseModel):
    """登录响应 —— 包含 token 和用户信息，前端无需二次请求 /me"""

    access_token: str
    token_type: str = "bearer"
    expires_in: int = Field(default=7200, description="过期时间（秒），默认 2 小时")
    user: "UserMeResponse"


class UserMeResponse(BaseModel):
    """当前用户信息（含角色和权限）"""

    id: UUID
    username: str
    phone: str | None = None
    email: str | None = None
    display_name: str
    status: UserStatus
    roles: list[str] = Field(default_factory=list, description="角色 code 列表")
    permissions: list[str] = Field(default_factory=list, description="权限 code 列表")


# ============================================================
# 角色分配
# ============================================================


class AssignRolesRequest(BaseModel):
    """为用户分配角色请求"""

    role_ids: list[UUID] = Field(min_length=1, description="角色 ID 列表")
