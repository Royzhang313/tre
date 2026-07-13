"""FastAPI 应用入口 —— ERP Builder"""

import logging
from contextlib import asynccontextmanager

from sqlalchemy import text

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api.v1 import _load_module_routers, register_exception_handlers

# 预加载所有业务模块（触发 ModuleRegistry + 路由注册）
_preload_modules = [
    "app.modules.auth", "app.modules.basedata", "app.modules.brand",
    "app.modules.purchase_contract", "app.modules.sales_contract",
    "app.modules.shipping", "app.modules.finance", "app.modules.system",
    "app.modules.recycle_bin", "app.modules.audit", "app.modules.inventory", "app.ai",
]
for _mod in _preload_modules:
    __import__(_mod)
from app.api.v1 import router as v1_router
from app.core.config import settings

logger = logging.getLogger(__name__)


def _auto_migrate(conn):
    """自动添加缺失的列 —— 从 SQLAlchemy 模型反射，对比 DB 自动补列"""
    import sqlite3
    if not isinstance(conn.connection.dbapi_connection, sqlite3.Connection):
        return

    from app.core.database import Base
    from sqlalchemy import inspect as sa_inspect

    inspector = sa_inspect(conn)
    dialect = conn.dialect

    for table_name, table in Base.metadata.tables.items():
        try:
            existing = {c["name"] for c in inspector.get_columns(table_name)}
        except Exception:
            continue

        for col in table.columns:
            if col.name not in existing:
                try:
                    col_type = col.type.compile(dialect)
                    nullable = "" if col.nullable else " NOT NULL"
                    default_sql = ""
                    if col.default:
                        default_sql = f" DEFAULT {col.default.arg}"
                    sql = f"ALTER TABLE {table_name} ADD COLUMN {col.name} {col_type}{nullable}{default_sql}"
                    conn.execute(text(sql))
                    conn.commit()
                    logger.info(f"Auto-migrate: added {table_name}.{col.name}")
                except Exception:
                    pass  # 列已存在或其他错误，跳过


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时：创建表 → 初始化 Seed
    try:
        from app.core.database import Base, engine
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
            # 自动添加缺失的列（SQLite 不支持 ALTER COLUMN，只处理 ADD COLUMN）
            await conn.run_sync(_auto_migrate)
        from app.modules.auth.seed import SeedManager
        await SeedManager.run()
        logger.info("数据库表创建 + Seed 初始化完成")
    except Exception:
        logger.warning("数据库初始化失败", exc_info=True)
    yield
    # 关闭时：清理资源、释放连接池


app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册领域异常处理器
register_exception_handlers(app)

# 注册 API v1 路由
app.include_router(v1_router)

# 加载所有已注册模块的路由（模块的 __init__.py 在 import 时会调用 modules.register()）
_load_module_routers()

# 静态文件服务 —— 上传文件访问
import os
uploads_dir = "/home/zy/workspace/tre/uploads"
os.makedirs(uploads_dir, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=uploads_dir), name="uploads")


@app.get("/")
async def root():
    """根路径"""
    return {"message": f"欢迎使用 {settings.app_name} API"}

