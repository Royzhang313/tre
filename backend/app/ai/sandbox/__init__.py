"""Sandbox —— AI 生成模块隔离测试环境"""

from app.ai.sandbox.models import PromotionRequest, SandboxInstance, SandboxTestResult
from app.ai.sandbox.service import SandboxService

__all__ = ["SandboxInstance", "SandboxTestResult", "PromotionRequest", "SandboxService"]
