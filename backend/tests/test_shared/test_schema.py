"""分页和 Schema 单元测试"""

import pytest
from pydantic import ValidationError

from app.shared.base_schema import APIResponse, PageRequest, PageResponse
from app.shared.pagination import PageParams


class TestPageParams:
    """PageParams 测试"""

    def test_from_request(self):
        """从 PageRequest 正确计算 offset"""
        req = PageRequest(page=3, page_size=20)
        params = PageParams.from_request(req)
        assert params.page == 3
        assert params.page_size == 20
        assert params.offset == 40  # (3-1)*20
        assert params.limit == 20

    def test_first_page_zero_offset(self):
        """第一页 offset 为 0"""
        req = PageRequest(page=1, page_size=50)
        params = PageParams.from_request(req)
        assert params.offset == 0


class TestPageRequest:
    """PageRequest 校验测试"""

    def test_defaults(self):
        """默认值"""
        req = PageRequest()
        assert req.page == 1
        assert req.page_size == 20

    def test_page_min_1(self):
        """页码不能小于 1"""
        with pytest.raises(ValidationError):
            PageRequest(page=0)

    def test_page_size_max_100(self):
        """每页最多 100"""
        with pytest.raises(ValidationError):
            PageRequest(page_size=101)


class TestPageResponse:
    """PageResponse 测试"""

    def test_from_list(self):
        """从列表构造分页响应"""
        items = ["a", "b", "c"]
        resp = PageResponse.from_list(items, total=10, page=2, page_size=3)
        assert resp.items == items
        assert resp.total == 10
        assert resp.page == 2
        assert resp.page_size == 3
        assert resp.pages == 4  # ceil(10/3)

    def test_empty_list(self):
        """空列表"""
        resp = PageResponse.from_list([], total=0, page=1, page_size=20)
        assert resp.items == []
        assert resp.total == 0
        assert resp.pages == 0


class TestAPIResponse:
    """APIResponse 测试"""

    def test_ok(self):
        """成功响应"""
        resp = APIResponse.ok({"id": 1})
        assert resp.code == 0
        assert resp.message == "success"
        assert resp.data == {"id": 1}

    def test_fail(self):
        """失败响应"""
        resp = APIResponse.fail(code=404, message="未找到")
        assert resp.code == 404
        assert resp.message == "未找到"
        assert resp.data is None

    def test_generic_type(self):
        """泛型支持"""
        resp: APIResponse[list[int]] = APIResponse.ok([1, 2, 3])
        assert resp.data == [1, 2, 3]
