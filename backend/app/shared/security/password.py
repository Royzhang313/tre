"""密码哈希工具 —— bcrypt 封装

所有模块统一使用此工具，不直接调用 bcrypt。
"""

import bcrypt


class PasswordHasher:
    """bcrypt 密码哈希器"""

    @staticmethod
    def hash(plain: str) -> str:
        """哈希明文密码"""
        return bcrypt.hashpw(plain.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify(plain: str, hashed: str) -> bool:
        """验证明文密码与哈希值"""
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
