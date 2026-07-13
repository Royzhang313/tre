"""Auth 模块 —— Service 层单元测试

使用 mock Repository，不依赖数据库。
"""

from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

import pytest

from app.core.exceptions import ConflictError, UnauthorizedError
from app.modules.auth.models import User, UserStatus
from app.modules.auth.schemas import (
    AssignRolesRequest,
    LoginResponse,
    RoleCreate,
    UserCreate,
    UserUpdate,
)
from app.modules.auth.service import AuthService, RoleService, UserService
from app.shared.security import JWTTokenManager, PasswordHasher

# ============================================================
# Fixtures
# ============================================================


def _mock_user(**overrides) -> User:
    """创建一个 mock User"""
    user = Mock(spec=User)
    user.id = uuid4()
    user.username = "testuser"
    user.email = "test@example.com"
    user.password_hash = PasswordHasher.hash("password123")
    user.phone = None
    user.display_name = "测试用户"
    user.status = UserStatus.ACTIVE
    user.last_login_at = None
    user.created_at = None
    user.updated_at = None
    user.user_roles = []
    for k, v in overrides.items():
        setattr(user, k, v)
    return user


# ============================================================
# AuthService
# ============================================================


class TestAuthServiceLogin:
    """登录测试"""

    @pytest.mark.asyncio
    async def test_login_success(self):
        user = _mock_user()
        repo = Mock()
        repo.get_by_username = AsyncMock(return_value=user)
        repo.update = AsyncMock()
        svc = AuthService(user_repo=repo)

        result = await svc.login("testuser", "password123")

        assert isinstance(result, LoginResponse)
        assert result.access_token
        assert result.user.username == "testuser"
        assert result.user.id == user.id

    @pytest.mark.asyncio
    async def test_login_user_not_found(self):
        repo = Mock()
        repo.get_by_username = AsyncMock(return_value=None)
        repo.get_by_phone = AsyncMock(return_value=None)
        svc = AuthService(user_repo=repo)

        with pytest.raises(UnauthorizedError, match="用户名或密码错误"):
            await svc.login("nobody", "any")

    @pytest.mark.asyncio
    async def test_login_wrong_password(self):
        user = _mock_user()
        repo = Mock()
        repo.get_by_username = AsyncMock(return_value=user)
        svc = AuthService(user_repo=repo)

        with pytest.raises(UnauthorizedError, match="用户名或密码错误"):
            await svc.login("testuser", "wrongpassword")

    @pytest.mark.asyncio
    async def test_login_inactive_user(self):
        user = _mock_user(status=UserStatus.INACTIVE)
        repo = Mock()
        repo.get_by_username = AsyncMock(return_value=user)
        svc = AuthService(user_repo=repo)

        with pytest.raises(UnauthorizedError, match="已停用"):
            await svc.login("testuser", "password123")

    @pytest.mark.asyncio
    async def test_login_locked_user(self):
        user = _mock_user(status=UserStatus.LOCKED)
        repo = Mock()
        repo.get_by_username = AsyncMock(return_value=user)
        svc = AuthService(user_repo=repo)

        with pytest.raises(UnauthorizedError, match="已锁定"):
            await svc.login("testuser", "password123")


class TestPasswordHasher:
    """PasswordHasher 测试"""

    def test_hash_and_verify(self):
        hashed = PasswordHasher.hash("secret123")
        assert hashed != "secret123"
        assert PasswordHasher.verify("secret123", hashed)

    def test_different_passwords(self):
        hashed = PasswordHasher.hash("aaa")
        assert not PasswordHasher.verify("bbb", hashed)


class TestJWTTokenManager:
    """JWTTokenManager 测试"""

    def test_create_and_verify(self):
        user = _mock_user()

        token = JWTTokenManager.create_token(user.id, user.username)
        payload = JWTTokenManager.verify(token)

        assert payload["sub"] == str(user.id)
        assert payload["username"] == "testuser"

    def test_invalid_token(self):
        with pytest.raises(UnauthorizedError, match="无效的访问令牌"):
            JWTTokenManager.verify("not.a.real.token")


# ============================================================
# UserService
# ============================================================


class TestUserServiceCreate:
    """创建用户测试"""

    @pytest.mark.asyncio
    async def test_create_success(self):
        user_repo = Mock()
        user_repo.get_by_username = AsyncMock(return_value=None)
        user_repo.get_by_email = AsyncMock(return_value=None)
        user_repo.create = AsyncMock()
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        data = UserCreate(
            username="newuser", email="new@test.com",
            password="password123", display_name="新用户",
        )
        # 拦截 User 构造——验证 create 被调用
        with patch("app.modules.auth.service.User", wraps=User):
            await svc.create_user(data)

        user_repo.create.assert_called_once()

    @pytest.mark.asyncio
    async def test_duplicate_username(self):
        user_repo = Mock()
        user_repo.get_by_username = AsyncMock(return_value=_mock_user())
        user_repo.get_by_email = AsyncMock(return_value=None)
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        data = UserCreate(
            username="existing", email="new@test.com",
            password="password123", display_name="X",
        )
        with pytest.raises(ConflictError, match="用户名已存在"):
            await svc.create_user(data)

    @pytest.mark.asyncio
    async def test_duplicate_email(self):
        user_repo = Mock()
        user_repo.get_by_username = AsyncMock(return_value=None)
        user_repo.get_by_email = AsyncMock(return_value=_mock_user())
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        data = UserCreate(
            username="new", email="existing@test.com",
            password="password123", display_name="X",
        )
        with pytest.raises(ConflictError, match="邮箱已存在"):
            await svc.create_user(data)


class TestUserServiceUpdate:
    """更新用户测试"""

    @pytest.mark.asyncio
    async def test_update_display_name(self):
        user = _mock_user()
        user_repo = Mock()
        user_repo.get_by_id_or_raise = AsyncMock(return_value=user)
        user_repo.get_by_email = AsyncMock(return_value=None)
        user_repo.update = AsyncMock()
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        result = await svc.update_user(user.id, UserUpdate(display_name="新名字"))
        assert result.display_name == "新名字"


class TestUserServiceChangeStatus:
    """状态变更测试"""

    @pytest.mark.asyncio
    async def test_cannot_change_self(self):
        uid = uuid4()
        user_repo = Mock()
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        with pytest.raises(ConflictError, match="不能修改自己的状态"):
            await svc.change_status(uid, UserStatus.INACTIVE, operator_id=uid)

    @pytest.mark.asyncio
    async def test_change_other_user(self):
        uid = uuid4()
        operator_id = uuid4()
        user = _mock_user(id=uid)
        user_repo = Mock()
        user_repo.get_by_id_or_raise = AsyncMock(return_value=user)
        user_repo.update = AsyncMock()
        role_repo = Mock()
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        result = await svc.change_status(uid, UserStatus.INACTIVE, operator_id=operator_id)
        assert result.status == UserStatus.INACTIVE


class TestUserServiceAssignRoles:
    """角色分配测试"""

    @pytest.mark.asyncio
    async def test_assign_roles(self):
        role_id = uuid4()
        user = _mock_user()
        user_repo = Mock()
        user_repo.get_by_id_or_raise = AsyncMock(return_value=user)
        user_repo.update = AsyncMock()
        role_repo = Mock()
        role_repo.exists = AsyncMock(return_value=True)
        svc = UserService(user_repo=user_repo, role_repo=role_repo)

        data = AssignRolesRequest(role_ids=[role_id])
        operator_id = uuid4()

        await svc.assign_roles(user.id, data, operator_id=operator_id)
        role_repo.exists.assert_called()


# ============================================================
# RoleService
# ============================================================


class TestRoleServiceDelete:
    """删除角色测试"""

    @pytest.mark.asyncio
    async def test_cannot_delete_system_role(self):
        role = Mock()
        role.is_system = True
        role.code = "admin"
        role_repo = Mock()
        role_repo.get_by_id_or_raise = AsyncMock(return_value=role)
        perm_repo = Mock()
        svc = RoleService(role_repo=role_repo, perm_repo=perm_repo)

        with pytest.raises(ConflictError, match="系统内置角色"):
            await svc.delete_role(uuid4())


class TestRoleServiceCreate:
    """创建角色测试"""

    @pytest.mark.asyncio
    async def test_duplicate_code(self):
        role_repo = Mock()
        role_repo.get_by_code = AsyncMock(return_value=Mock())
        perm_repo = Mock()
        svc = RoleService(role_repo=role_repo, perm_repo=perm_repo)

        with pytest.raises(ConflictError, match="角色编码已存在"):
            await svc.create_role(RoleCreate(code="admin", name="管理员"))
