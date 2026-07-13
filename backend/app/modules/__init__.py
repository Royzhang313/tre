"""Vertical Slice 模块容器

每个业务模块通过 register() 注册自己的 FastAPI Router，
模块之间通过 EventBus 通信，不允许直接调用对方的 Service。

使用示例:
    # 在模块的 __init__.py 中
    from app.modules import register
    from .router import router

    register("purchase", router)
"""

from fastapi import APIRouter

#: 已注册模块列表: [(模块名, router)]
_registered: list[tuple[str, APIRouter]] = []


def register(module_name: str, router: APIRouter) -> None:
    """注册模块路由

    Args:
        module_name: 模块名称（BaseData, Purchase, Inventory 等）
        router: 模块的 FastAPI APIRouter 实例
    """
    _registered.append((module_name, router))


def get_registered_modules() -> list[tuple[str, APIRouter]]:
    """获取所有已注册的模块"""
    return list(_registered)
