"""API v1 路由聚合 —— 加载所有已注册模块的路由 + 全局异常处理"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from app.core.exceptions import (
    BusinessRuleViolationError,
    ConflictError,
    DomainError,
    ForbiddenError,
    NotFoundError,
    UnauthorizedError,
    ValidationError,
)
from app.modules import get_registered_modules

router = APIRouter(prefix="/api/v1")


# ============================================================
# 领域异常 → API 响应映射
# ============================================================

EXCEPTION_HANDLERS: dict[type[DomainError], int] = {
    NotFoundError: 404,
    ValidationError: 422,
    ConflictError: 409,
    UnauthorizedError: 401,
    ForbiddenError: 403,
    BusinessRuleViolationError: 422,
}


@router.get("/health")
async def health_check():
    """健康检查端点"""
    return {"status": "ok", "version": "0.1.0"}


# ============================================================
# 加载模块路由
# ============================================================

def _load_module_routers():
    """将已注册模块的路由挂载到 v1 router（模块 Router 自带 prefix）"""
    for _module_name, module_router in get_registered_modules():
        router.include_router(module_router)
    # 系统 API + AI Builder + 事件历史 + 动态 UI + 仪表盘
    from app.ai.router import router as ai_router
    from app.ai.ui.router import router as ui_router
    from app.api.v1.dashboard import router as dashboard_router
    from app.api.v1.events import router as events_router
    from app.api.v1.system import router as system_router
    router.include_router(dashboard_router)
    router.include_router(system_router)
    router.include_router(ai_router)
    router.include_router(ui_router)
    router.include_router(events_router)


# ============================================================
# 注册异常处理器
# ============================================================

def register_exception_handlers(app):
    """在 FastAPI app 上注册领域异常处理器"""

    # 工厂函数 —— 正确捕获 exc_class 和 status_code，避免闭包陷阱
    def _make_handler(exc_cls: type, status: int):
        @app.exception_handler(exc_cls)
        async def handler(request: Request, exc: DomainError):
            return JSONResponse(
                status_code=status,
                content={
                    "code": status,
                    "message": exc.message,
                    "details": exc.details or {},
                },
            )
        return handler

    for exc_class, status_code in EXCEPTION_HANDLERS.items():
        _make_handler(exc_class, status_code)

    # 兜底: 未知领域异常
    @app.exception_handler(DomainError)
    async def domain_error_handler(request: Request, exc: DomainError):
        return JSONResponse(
            status_code=500,
            content={
                "code": 500,
                "message": exc.message,
                "details": exc.details or {},
            },
        )
