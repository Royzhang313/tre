"""CurrentUser 上下文 —— 请求级用户信息（一次加载，多处复用）

不依赖 ORM relationship，所有数据通过 Repository JOIN 查询后封装。
"""

from dataclasses import dataclass, field
from uuid import UUID

from app.modules.auth.models import UserStatus


@dataclass(frozen=True, slots=True)
class CurrentUser:
    """当前请求用户上下文

    在 get_current_user 依赖中一次构建，后续 require_permission 和端点直接使用。
    permission_codes 使用 frozenset —— O(1) 查找，不可变。
    """

    id: UUID
    username: str
    email: str
    display_name: str
    status: UserStatus
    role_codes: frozenset[str] = field(default_factory=frozenset)
    permission_codes: frozenset[str] = field(default_factory=frozenset)

    def has_permission(self, code: str) -> bool:
        """检查是否拥有指定权限 —— O(1)"""
        return code in self.permission_codes

    def has_role(self, code: str) -> bool:
        """检查是否拥有指定角色 —— O(1)"""
        return code in self.role_codes

    def is_active(self) -> bool:
        """是否为活跃状态"""
        return self.status == UserStatus.ACTIVE
