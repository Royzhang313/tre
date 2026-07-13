"""共享类型定义 —— DDD 通用基础类型"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID

# 实体 ID 类型
EntityId = UUID

# 金额类型（财务精度）
Money = Decimal

# 时间戳类型
Timestamp = datetime
