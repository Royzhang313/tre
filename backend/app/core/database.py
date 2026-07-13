"""数据库引擎 & 异步会话工厂"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings

# ---- 数据库引擎配置 ----
# 根据数据库类型设置不同的连接池参数
_is_sqlite = settings.database_url.startswith("sqlite")

# SQLite 仅支持单写者，pool_size 必须为 1，否则会报 "database is locked"
_engine_kwargs: dict = {
    "echo": settings.debug,
    "pool_pre_ping": True,            # 使用前先 ping，检测并丢弃已断开的连接
    "pool_recycle": 3600,             # 连接存活超过 1 小时后自动回收，防止数据库端主动断开
    "pool_size": 1 if _is_sqlite else 5,
    "max_overflow": 0 if _is_sqlite else 10,
    "pool_timeout": 30,               # 等待连接池可用连接的超时时间（秒）
}

if _is_sqlite:
    _engine_kwargs["connect_args"] = {"check_same_thread": False}

# 异步引擎
engine = create_async_engine(settings.database_url, **_engine_kwargs)

# 异步会话工厂
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """SQLAlchemy 声明式基类 —— 所有 ORM 模型继承此类"""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI 依赖注入 —— 获取数据库会话"""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
