"""轻量依赖注入容器

M0 阶段提供简单的服务注册/获取，后续可替换为 python-dependency-injector。

使用示例:
    # 注册服务（通常在模块初始化时）
    di.register("inventory_service", InventoryService())

    # 获取服务
    service = di.get("inventory_service", InventoryService)
"""

from typing import Any, TypeVar

T = TypeVar("T")

_registry: dict[str, Any] = {}


class DIContainer:
    """轻量服务容器"""

    @staticmethod
    def register(name: str, instance: Any) -> None:
        """注册服务实例

        Args:
            name: 服务名称（推荐使用模块名.服务名）
            instance: 服务实例（通常是单例）
        """
        _registry[name] = instance

    @staticmethod
    def get(name: str, expected_type: type[T] | None = None) -> T:
        """获取已注册的服务实例

        Args:
            name: 服务名称
            expected_type: 期望类型（运行时校验，M0 仅做文档说明）

        Returns:
            服务实例

        Raises:
            KeyError: 服务未注册
        """
        if name not in _registry:
            raise KeyError(f"服务 '{name}' 未注册，可用的服务: {list(_registry.keys())}")
        instance = _registry[name]
        return instance  # type: ignore[return-value]

    @staticmethod
    def unregister(name: str) -> None:
        """注销服务（仅在测试中使用）"""
        _registry.pop(name, None)

    @staticmethod
    def clear() -> None:
        """清空所有注册（仅在测试中使用）"""
        _registry.clear()

    @staticmethod
    def list_services() -> list[str]:
        """列出所有已注册的服务名"""
        return list(_registry.keys())


# 全局单例
di = DIContainer()
