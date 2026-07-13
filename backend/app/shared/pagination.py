"""分页工具

将 PageRequest 转换为 SQLAlchemy offset/limit 参数。

使用示例:
    params = PageParams.from_request(page_request)
    items = await repo.list(offset=params.offset, limit=params.limit)
    total = await repo.count()
    return PageResponse.from_list(items, total, params.page, params.page_size)
"""

from dataclasses import dataclass

from app.shared.base_schema import PageRequest


@dataclass(frozen=True, slots=True)
class PageParams:
    """内部使用的分页参数"""

    page: int
    page_size: int
    offset: int
    limit: int

    @classmethod
    def from_request(cls, req: PageRequest) -> "PageParams":
        """从 PageRequest 构造"""
        offset = (req.page - 1) * req.page_size
        return cls(
            page=req.page,
            page_size=req.page_size,
            offset=offset,
            limit=req.page_size,
        )


async def paginate(repository, page_request: PageRequest):
    """通用分页查询——一次调用完成列表+计数

    Returns:
        PageResponse
    """
    params = PageParams.from_request(page_request)
    items = await repository.list(offset=params.offset, limit=params.limit)
    total = await repository.count()
    from app.shared.base_schema import PageResponse

    return PageResponse.from_list(items, total, params.page, params.page_size)
