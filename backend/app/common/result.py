"""Result[T] 模式 —— 避免用异常做流程控制

使用示例:
    def divide(a: int, b: int) -> Result[float]:
        if b == 0:
            return Failure("除数不能为零", "DIVISION_BY_ZERO")
        return Success(a / b)

    result = divide(10, 2)
    if result.is_success:
        print(result.value)
    else:
        print(result.error)
"""

from dataclasses import dataclass, field
from typing import TypeVar

T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class Success[T]:
    """成功结果"""

    value: T

    @property
    def is_success(self) -> bool:
        return True

    @property
    def is_failure(self) -> bool:
        return False


@dataclass(frozen=True, slots=True)
class Failure:
    """失败结果"""

    error: str
    error_code: str = "UNKNOWN_ERROR"
    details: dict | None = field(default=None, compare=False)

    @property
    def is_success(self) -> bool:
        return False

    @property
    def is_failure(self) -> bool:
        return True


# Result 联合类型
Result = Success[T] | Failure
