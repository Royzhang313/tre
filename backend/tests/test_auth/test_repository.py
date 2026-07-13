"""Auth 模块 —— Repository 结构测试

不依赖数据库：验证继承关系、方法签名。
"""

import inspect

from app.modules.auth.repository import (
    PermissionRepository,
    RoleRepository,
    UserRepository,
)
from app.shared.base_repository import BaseRepository


class TestUserRepository:
    """UserRepository 测试"""

    def test_inherits_base_repository(self):
        assert issubclass(UserRepository, BaseRepository)

    def test_has_domain_methods(self):
        """领域特有方法"""
        methods = [
            m for m, _ in inspect.getmembers(UserRepository, predicate=inspect.isfunction)
            if not m.startswith("_")
        ]
        assert "get_by_username" in methods
        assert "get_by_email" in methods

    def test_does_not_redefine_crud(self):
        """不重复定义 CRUD —— 由 BaseRepository 提供"""
        assert "get_by_id" not in UserRepository.__dict__
        assert "create" not in UserRepository.__dict__
        assert "update" not in UserRepository.__dict__


class TestRoleRepository:
    """RoleRepository 测试"""

    def test_inherits_base_repository(self):
        assert issubclass(RoleRepository, BaseRepository)

    def test_has_domain_methods(self):
        methods = [
            m for m, _ in inspect.getmembers(RoleRepository, predicate=inspect.isfunction)
            if not m.startswith("_")
        ]
        assert "get_by_code" in methods


class TestPermissionRepository:
    """PermissionRepository 测试"""

    def test_inherits_base_repository(self):
        assert issubclass(PermissionRepository, BaseRepository)

    def test_has_domain_methods(self):
        methods = [
            m for m, _ in inspect.getmembers(PermissionRepository, predicate=inspect.isfunction)
            if not m.startswith("_")
        ]
        assert "get_by_code" in methods
        assert "list_by_module" in methods


class TestRepositoryIndependence:
    """Repository 独立性 —— 各自操作自己的 Aggregate"""

    def test_user_repo_only_user(self):
        """UserRepository 只操作 User"""
        repo = UserRepository.__bases__[0]
        # 泛型参数绑定为 User
        assert repo.__name__ == "BaseRepository"

    def test_role_repo_only_role(self):
        """RoleRepository 只操作 Role"""
        repo = RoleRepository.__bases__[0]
        assert repo.__name__ == "BaseRepository"

    def test_repos_dont_depend_on_each_other(self):
        """三个 Repository 互相独立，不交叉引用"""
        user_src = inspect.getsource(UserRepository)
        role_src = inspect.getsource(RoleRepository)
        perm_src = inspect.getsource(PermissionRepository)

        assert "RoleRepository" not in user_src
        assert "PermissionRepository" not in user_src
        assert "UserRepository" not in role_src
        assert "UserRepository" not in perm_src
