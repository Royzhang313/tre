"""Attachment Storage —— 附件存储接口（Protocol）

M1 仅定义接口，具体实现（MinIO、S3、本地文件等）在业务模块中注入。

预留 metadata（mime、size、hash、storage_provider、storage_key），
切换存储后端（MinIO → OSS → S3）无需修改接口。
"""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID


@dataclass(frozen=True, slots=True)
class AttachmentMeta:
    """附件元数据

    Attributes:
        mime: MIME 类型，例如 "application/pdf"
        size: 文件大小（字节）
        hash_sha256: SHA-256 哈希值
        category: 附件分类，例如 "contract" / "invoice" / "photo"
        storage_provider: 存储后端标识，例如 "minio" / "s3" / "oss" / "local"
        storage_key: 存储路径，例如 "attachment/2026/07/contract.pdf"
    """

    mime: str
    size: int
    hash_sha256: str
    category: str | None = None
    storage_provider: str = "local"
    storage_key: str = ""


class AttachmentStorage(Protocol):
    """附件存储接口 —— 所有模块通过此接口管理附件

    后续提供 MinIO / S3 / Local 等多种实现。
    """

    async def upload(
        self,
        file_name: str,
        content: bytes,
        entity_type: str,
        entity_id: UUID,
        meta: AttachmentMeta,
    ) -> UUID:
        """上传附件，返回 attachment_id"""
        ...

    async def download(self, attachment_id: UUID) -> tuple[str, bytes] | None:
        """下载附件，返回 (file_name, content)，不存在返回 None"""
        ...

    async def get_meta(self, attachment_id: UUID) -> AttachmentMeta | None:
        """获取附件元数据"""
        ...

    async def list_by_entity(
        self, entity_type: str, entity_id: UUID
    ) -> list[dict]:
        """列出实体关联的所有附件摘要"""
        ...

    async def delete(self, attachment_id: UUID) -> None:
        """删除附件"""
        ...
