"""Attachment 附件模块 —— M1 仅定义接口

后续提供 MinIO / S3 / Local 等具体实现。
"""

from app.shared.attachment.registry import AttachmentMeta, AttachmentStorage

__all__ = [
    "AttachmentMeta",
    "AttachmentStorage",
]
