"""Auth 模块 —— Schemas 单元测试

不依赖数据库：仅验证 Pydantic 校验规则。
"""

from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.modules.auth.models import UserStatus
from app.modules.auth.schemas import (
    AssignRolesRequest,
    LoginRequest,
    LoginResponse,
    RoleCreate,
    RoleUpdate,
    UserCreate,
    UserMeResponse,
    UserStatusUpdate,
    UserUpdate,
)


class TestUserCreate:
    """UserCreate 校验测试"""

    def test_valid(self):
        schema = UserCreate(
            username="testuser",
            email="test@example.com",
            password="password123",
            display_name="测试用户",
        )
        assert schema.username == "testuser"
        assert schema.email == "test@example.com"

    def test_username_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(username="a", email="a@b.com", password="12345678", display_name="X")

    def test_username_too_long(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="a" * 51, email="a@b.com", password="12345678", display_name="X"
            )

    def test_password_too_short(self):
        with pytest.raises(ValidationError):
            UserCreate(
                username="valid", email="a@b.com", password="", display_name="X"
            )


class TestUserUpdate:
    """UserUpdate 校验测试 —— 仅资料修改，不含 status"""

    def test_all_fields_optional(self):
        """全部字段可选 —— 支持部分更新"""
        schema = UserUpdate()
        assert schema.email is None
        assert schema.display_name is None

    def test_partial_update(self):
        schema = UserUpdate(display_name="新名字")
        assert schema.display_name == "新名字"
        assert schema.email is None

    def test_no_status_field(self):
        """UserUpdate 不包含 status 字段 —— status 独立操作，由 UserStatusUpdate 负责"""
        assert "status" not in UserUpdate.model_fields


class TestUserStatusUpdate:
    """UserStatusUpdate 校验测试 —— status 独立操作"""

    def test_valid(self):
        schema = UserStatusUpdate(status=UserStatus.INACTIVE)
        assert schema.status == UserStatus.INACTIVE

    def test_required(self):
        """status 字段必填"""
        with pytest.raises(ValidationError):
            UserStatusUpdate()  # type: ignore[call-arg]


class TestRoleCreate:
    """RoleCreate 校验测试"""

    def test_valid(self):
        schema = RoleCreate(code="admin", name="管理员")
        assert schema.code == "admin"

    def test_code_too_short(self):
        with pytest.raises(ValidationError):
            RoleCreate(code="a", name="管理员")


class TestRoleUpdate:
    """RoleUpdate 校验测试"""

    def test_all_optional(self):
        schema = RoleUpdate()
        assert schema.name is None


class TestLoginRequest:
    """LoginRequest 校验测试"""

    def test_valid(self):
        schema = LoginRequest(username="admin", password="secret")
        assert schema.username == "admin"

    def test_empty_username(self):
        with pytest.raises(ValidationError):
            LoginRequest(username="", password="secret")


class TestLoginResponse:
    """LoginResponse 测试"""

    def test_with_user(self):
        uid = uuid4()
        user = UserMeResponse(
            id=uid,
            username="admin",
            email="admin@test.com",
            display_name="管理员",
            status=UserStatus.ACTIVE,
        )
        resp = LoginResponse(access_token="eyJ...", user=user)
        assert resp.access_token == "eyJ..."
        assert resp.token_type == "bearer"
        assert resp.expires_in == 7200
        assert resp.user.username == "admin"
        assert resp.user.id == uid


class TestUserMeResponse:
    """UserMeResponse 测试"""

    def test_default_lists(self):
        uid = uuid4()
        resp = UserMeResponse(
            id=uid,
            username="admin",
            email="admin@test.com",
            display_name="管理员",
            status=UserStatus.ACTIVE,
        )
        assert resp.roles == []
        assert resp.permissions == []


class TestAssignRolesRequest:
    """AssignRolesRequest 校验测试"""

    def test_valid(self):
        role_ids = [uuid4(), uuid4()]
        schema = AssignRolesRequest(role_ids=role_ids)
        assert len(schema.role_ids) == 2

    def test_empty_list(self):
        with pytest.raises(ValidationError):
            AssignRolesRequest(role_ids=[])
