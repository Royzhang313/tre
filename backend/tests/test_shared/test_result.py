"""Result[T] 类型单元测试"""

import pytest

from app.common.result import Failure, Success


class TestResult:
    """Result[T] 模式测试"""

    def test_success_value(self):
        """Success 包装值"""
        result = Success(42)
        assert result.value == 42
        assert result.is_success is True
        assert result.is_failure is False

    def test_success_with_dict(self):
        """Success 包装复杂对象"""
        result = Success({"name": "test"})
        assert result.value["name"] == "test"

    def test_failure(self):
        """Failure 包装错误信息"""
        result = Failure("出错了", "ERR_001")
        assert result.error == "出错了"
        assert result.error_code == "ERR_001"
        assert result.is_success is False
        assert result.is_failure is True

    def test_failure_default_code(self):
        """Failure 默认错误码"""
        result = Failure("出错了")
        assert result.error_code == "UNKNOWN_ERROR"

    def test_failure_details(self):
        """Failure 带详情"""
        result = Failure("出错了", details={"reason": "test"})
        assert result.details == {"reason": "test"}

    def test_success_immutable(self):
        """Success 不可变"""
        result = Success(42)
        with pytest.raises(Exception):
            result.value = 99  # type: ignore

    def test_failure_immutable(self):
        """Failure 不可变"""
        result = Failure("出错了")
        with pytest.raises(Exception):
            result.error = "改了"  # type: ignore

    def test_pattern_matching(self):
        """支持 match/case 模式匹配"""

        def process(result):
            match result:
                case Success(value):
                    return f"成功: {value}"
                case Failure(error, code):
                    return f"失败[{code}]: {error}"

        assert process(Success("done")) == "成功: done"
        assert process(Failure("超时", "TIMEOUT")) == "失败[TIMEOUT]: 超时"
