"""通用 Pydantic Schema

- APIResponse[T]: 统一响应格式
- PageRequest: 分页请求参数
- PageResponse[T]: 分页响应
- FilterSchema: 过滤基类（业务模块继承，Repository 不消费）
- SortSchema: 多字段排序基类
"""

from typing import TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class APIResponse[T](BaseModel):
    """统一 API 响应格式

    Example:
        {
            "code": 0,
            "message": "success",
            "data": { ... }
        }
    """

    code: int = Field(default=0, description="业务状态码，0 表示成功")
    message: str = Field(default="success", description="提示信息")
    data: T | None = Field(default=None, description="响应数据")

    @classmethod
    def ok(cls, data: T, message: str = "success") -> "APIResponse[T]":
        """快捷构造成功响应"""
        return cls(code=0, message=message, data=data)

    @classmethod
    def fail(cls, code: int, message: str) -> "APIResponse[None]":
        """快捷构造失败响应"""
        return APIResponse[None](code=code, message=message, data=None)


class PageRequest(BaseModel):
    """分页请求参数"""

    page: int = Field(default=1, ge=1, description="页码，从 1 开始")
    page_size: int = Field(default=50, ge=1, le=200, description="每页记录数，默认50")
    sort_by: str | None = Field(default=None, description="排序字段")
    sort_order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")


class PageResponse[T](BaseModel):
    """分页响应"""

    items: list[T] = Field(default_factory=list, description="当前页数据")
    total: int = Field(default=0, description="总记录数")
    page: int = Field(default=1, description="当前页码")
    page_size: int = Field(default=20, description="每页记录数")
    pages: int = Field(default=0, description="总页数")

    @classmethod
    def from_list(
        cls, items: list[T], total: int, page: int, page_size: int
    ) -> "PageResponse[T]":
        """从列表和分页参数构造"""
        pages = (total + page_size - 1) // page_size if page_size > 0 else 0
        return cls(items=items, total=total, page=page, page_size=page_size, pages=pages)


# ============================================================
# M1 新增: Filter / Sort 基类
# ============================================================


class FilterSchema(BaseModel):
    """过滤基类 —— 业务模块继承此类定义自己的过滤条件

    Shared Layer 只定义 Schema 结构，不消费它。
    具体过滤 → SQL 条件的转换在业务 Service 层完成。::

        class ProductFilter(FilterSchema):
            status: str | None = None
            category_id: UUID | None = None
    """

    search: str | None = Field(default=None, description="通用搜索关键词")


class SortSchema(BaseModel):
    """多字段排序基类

    格式: "field1,-field2" → field1 ASC, field2 DESC::

        sort = SortSchema(sort_by="name,-created_at")
    """

    sort_by: str | None = Field(
        default=None,
        description="排序字段，逗号分隔，- 前缀表示降序。例如 'name,-created_at'",
    )
