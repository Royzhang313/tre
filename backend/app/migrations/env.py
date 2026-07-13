"""Alembic 迁移环境配置 —— 使用 app.core.config 加载数据库 URL"""

import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

# 加载应用配置
from app.core.config import settings
from app.core.database import Base

# Alembic Config 对象
config = context.config

# 用应用配置覆盖 alembic.ini 中的数据库 URL
config.set_main_option("sqlalchemy.url", settings.database_url)

# 配置日志
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# 自动生成迁移时使用的元数据 —— 导入所有模型后自动包含
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """离线模式 —— 生成 SQL 脚本而非直接连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """在给定连接上执行迁移"""
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """异步在线模式 —— 通过 async engine 连接数据库执行迁移"""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


def run_migrations_online() -> None:
    """在线模式入口"""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
