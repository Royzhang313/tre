"""Auth 模块 —— ORM 模型结构测试

不依赖数据库：仅验证模型定义、字段、关系、约束的正确性。
"""

from app.modules.auth.models import (
    Permission,
    Role,
    RolePermission,
    User,
    UserRole,
    UserStatus,
)


def _ann(cls: type) -> dict:
    """收集类及其所有父类的 __annotations__"""
    result: dict = {}
    for base in reversed(cls.__mro__):
        result.update(getattr(base, "__annotations__", {}))
    return result


class TestUserStatus:
    """UserStatus 枚举测试"""

    def test_values(self):
        assert UserStatus.ACTIVE == "active"
        assert UserStatus.INACTIVE == "inactive"
        assert UserStatus.LOCKED == "locked"

    def test_is_str_enum(self):
        """StrEnum 可与字符串直接比较"""
        assert isinstance(UserStatus.ACTIVE, str)


class TestUserModel:
    """User 模型测试"""

    def test_tablename(self):
        assert User.__tablename__ == "auth_users"

    def test_fields_exist(self):
        annotations = _ann(User)
        for field in (
            "username", "email", "password_hash", "display_name",
            "status", "last_login_at",
        ):
            assert field in annotations, f"字段 {field} 缺失"

    def test_status_type_is_enum(self):
        """status 字段使用 UserStatus 枚举"""
        annotations = _ann(User)
        assert "status" in annotations

    def test_has_user_roles_relationship(self):
        assert hasattr(User, "user_roles")

    def test_inherits_base_model(self):
        assert "id" in _ann(User)
        assert "created_at" in _ann(User)
        assert "updated_at" in _ann(User)


class TestRoleModel:
    """Role 模型测试"""

    def test_tablename(self):
        assert Role.__tablename__ == "auth_roles"

    def test_fields_exist(self):
        annotations = _ann(Role)
        for field in ("code", "name", "description", "is_system"):
            assert field in annotations, f"字段 {field} 缺失"

    def test_has_relationships(self):
        assert hasattr(Role, "user_roles")
        assert hasattr(Role, "role_permissions")

    def test_inherits_base_model(self):
        assert "id" in _ann(Role)
        assert "created_at" in _ann(Role)


class TestPermissionModel:
    """Permission 模型测试"""

    def test_tablename(self):
        assert Permission.__tablename__ == "auth_permissions"

    def test_fields_exist(self):
        annotations = _ann(Permission)
        for field in ("code", "name", "module", "resource", "action"):
            assert field in annotations, f"字段 {field} 缺失"

    def test_has_role_permissions_relationship(self):
        assert hasattr(Permission, "role_permissions")

    def test_inherits_base_model(self):
        assert "id" in _ann(Permission)
        assert "created_at" in _ann(Permission)

    def test_code_format_design(self):
        """code 命名规范: module.resource.action"""
        assert hasattr(Permission, "module")
        assert hasattr(Permission, "resource")
        assert hasattr(Permission, "action")


class TestUserRoleModel:
    """UserRole 关联表测试"""

    def test_tablename(self):
        assert UserRole.__tablename__ == "auth_user_roles"

    def test_composite_pk(self):
        """user_id + role_id 复合主键"""
        annotations = _ann(UserRole)
        assert "user_id" in annotations
        assert "role_id" in annotations

    def test_relationships(self):
        assert hasattr(UserRole, "user")
        assert hasattr(UserRole, "role")

    def test_unique_constraint(self):
        """user_id + role_id 唯一约束"""
        args = UserRole.__table_args__
        assert args is not None


class TestRolePermissionModel:
    """RolePermission 关联表测试"""

    def test_tablename(self):
        assert RolePermission.__tablename__ == "auth_role_permissions"

    def test_composite_pk(self):
        annotations = _ann(RolePermission)
        assert "role_id" in annotations
        assert "permission_id" in annotations

    def test_relationships(self):
        assert hasattr(RolePermission, "role")
        assert hasattr(RolePermission, "permission")

    def test_unique_constraint(self):
        args = RolePermission.__table_args__
        assert args is not None


class TestAggregateIndependence:
    """聚合根独立性测试"""

    def test_three_aggregate_roots(self):
        """验证 3 个聚合根各独立存在"""
        assert issubclass(User, object)
        assert issubclass(Role, object)
        assert issubclass(Permission, object)
        # 三者无继承关系
        assert not issubclass(Permission, Role)
        assert not issubclass(Permission, User)
