"""Preview API 异常隔离测试"""

import pytest

from app.ai.ui.preview import SandboxPreviewService


class TestPreviewMenuNoSandbox:
    """无 Sandbox 场景 —— 返回空列表"""

    @pytest.mark.asyncio
    async def test_returns_empty_items(self):
        result = await SandboxPreviewService.generate_preview_menu()
        assert "items" in result
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_no_exception(self):
        """不应抛出异常"""
        result = await SandboxPreviewService.generate_preview_menu()
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_format_compatible(self):
        """响应格式兼容前端"""
        result = await SandboxPreviewService.generate_preview_menu()
        assert "items" in result
        assert isinstance(result["items"], list)


class TestPreviewSchemaNoSandbox:
    """无 Sandbox 时 Schema 返回 None"""

    @pytest.mark.asyncio
    async def test_returns_none_for_missing(self):
        result = await SandboxPreviewService.generate_preview_schema("non-existent-id")
        assert result is None

    @pytest.mark.asyncio
    async def test_no_exception(self):
        """不应抛出异常"""
        result = await SandboxPreviewService.generate_preview_schema("any-id")
        assert result is None  # No DB = safe return


class TestPreviewIsolation:
    """Preview 异常不影响主 UI"""

    @pytest.mark.asyncio
    async def test_menu_never_throws(self):
        """generate_preview_menu 在任何情况下都不抛异常"""
        for _ in range(3):
            result = await SandboxPreviewService.generate_preview_menu()
            assert "items" in result

    @pytest.mark.asyncio
    async def test_schema_never_throws(self):
        """generate_preview_schema 在任何情况下都不抛异常"""
        result = await SandboxPreviewService.generate_preview_schema("any")
        assert result is None or isinstance(result, dict)
