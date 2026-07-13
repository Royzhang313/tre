"""依赖注入容器单元测试"""

import pytest

from app.core.di import DIContainer, di


class TestDIContainer:
    """DIContainer 功能测试"""

    def setup_method(self):
        """每个测试前清空"""
        DIContainer.clear()

    def teardown_method(self):
        DIContainer.clear()

    def test_register_and_get(self):
        """注册后可以获取"""

        class TestService:
            def greet(self):
                return "hello"

        service = TestService()
        di.register("test_service", service)
        retrieved = di.get("test_service")
        assert retrieved is service
        assert retrieved.greet() == "hello"

    def test_register_overwrite(self):
        """重复注册覆盖旧值"""
        di.register("svc", "old")
        di.register("svc", "new")
        assert di.get("svc") == "new"

    def test_get_not_registered(self):
        """获取未注册服务抛出 KeyError"""
        with pytest.raises(KeyError, match="未注册"):
            di.get("not_exist")

    def test_unregister(self):
        """注销后无法获取"""
        di.register("temp", "value")
        di.unregister("temp")
        with pytest.raises(KeyError):
            di.get("temp")

    def test_unregister_nonexistent(self):
        """注销不存在的服务不报错"""
        di.unregister("not_exist")  # 不抛异常

    def test_list_services(self):
        """列出所有已注册服务"""
        di.register("a", 1)
        di.register("b", 2)
        services = di.list_services()
        assert sorted(services) == ["a", "b"]

    def test_clear(self):
        """清空所有注册"""
        di.register("a", 1)
        di.register("b", 2)
        di.clear()
        assert di.list_services() == []
        with pytest.raises(KeyError):
            di.get("a")
