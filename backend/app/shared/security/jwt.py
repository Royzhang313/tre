"""JWT Token 管理 —— 签发和验证

所有模块统一使用此工具，不直接调用 python-jose。
"""

import os
from datetime import UTC, datetime
from uuid import UUID

from jose import JWTError, jwt

from app.core.exceptions import UnauthorizedError


class JWTTokenManager:
    """JWT Token 管理器

    SECRET_KEY 从环境变量 JWT_SECRET_KEY 读取，开发环境有默认值。
    """

    SECRET_KEY: str = os.getenv(
        "JWT_SECRET_KEY",
        "erp-builder-dev-secret--change-in-production",
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_SECONDS: int = int(
        os.getenv("JWT_EXPIRE_SECONDS", "7200")
    )

    @classmethod
    def create_token(cls, user_id: UUID, username: str) -> str:
        """生成 JWT access_token

        Args:
            user_id: 用户 ID
            username: 用户名

        Returns:
            签发的 JWT 字符串
        """
        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "username": username,
            "iat": now,
            "exp": now.timestamp() + cls.ACCESS_TOKEN_EXPIRE_SECONDS,
        }
        return jwt.encode(payload, cls.SECRET_KEY, algorithm=cls.ALGORITHM)

    @classmethod
    def verify(cls, token: str) -> dict:
        """验证 JWT，返回 payload

        Raises:
            UnauthorizedError: Token 无效或过期
        """
        try:
            return jwt.decode(token, cls.SECRET_KEY, algorithms=[cls.ALGORITHM])
        except JWTError:
            raise UnauthorizedError("无效的访问令牌")
