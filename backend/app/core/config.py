"""应用核心配置模块 —— 通过 Pydantic Settings 加载 .env 环境变量"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用全局配置，自动从 .env 文件加载"""

    # 应用
    app_name: str = "ERP Builder"
    app_version: str = "0.1.0"
    debug: bool = False

    # 数据库（默认 SQLite 开发模式，生产环境设 PostgreSQL URL）
    database_url: str = "sqlite+aiosqlite:////home/zy/workspace/tre/backend/erp_builder.db"

    # AI
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    default_ai_model: str = "deepseek-chat"

    # CORS
    cors_origins: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="allow",
    )


settings = Settings()
