"""System API —— AI Context + Capability Index + File Upload"""

import os
import uuid
from pathlib import Path

from fastapi import APIRouter, Query, UploadFile, File

from app.shared.base_schema import APIResponse
from app.shared.capability_registry import CapabilityRegistry
from app.shared.module_registry import ModuleRegistry

router = APIRouter(prefix="/system", tags=["系统"])

UPLOAD_DIR = Path("/home/zy/workspace/tre/uploads")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


@router.get("/modules")
async def list_modules():
    """所有已注册模块"""
    modules = ModuleRegistry.list_all()
    return APIResponse.ok([m.to_dict() for m in modules])


@router.get("/modules/{name}")
async def get_module(name: str):
    """模块详情"""
    manifest = ModuleRegistry.get(name)
    if manifest is None:
        return APIResponse.fail(404, f"模块 {name} 不存在")
    return APIResponse.ok(manifest.to_dict())


@router.get("/capabilities")
async def list_capabilities(q: str | None = Query(default=None), module: str | None = Query(default=None)):
    """能力列表（支持搜索）"""
    if q:
        caps = CapabilityRegistry.search(q)
    elif module:
        caps = CapabilityRegistry.list_by_module(module)
    else:
        caps = CapabilityRegistry.list_all()
    return APIResponse.ok([c.to_dict() for c in caps])


@router.get("/capabilities/{name}")
async def get_capability(name: str):
    """能力详情"""
    cap = CapabilityRegistry.get(name)
    if cap is None:
        return APIResponse.fail(404, f"能力 {name} 不存在")
    return APIResponse.ok(cap.to_dict())


@router.get("/capabilities/index")
async def capability_index():
    """AI 能力索引"""
    return APIResponse.ok(CapabilityRegistry.build_index())


@router.get("/ai-context")
async def ai_context():
    """AI Context 完整快照"""
    modules = [m.to_dict() for m in ModuleRegistry.list_all()]
    caps = CapabilityRegistry.build_index()
    return APIResponse.ok({
        "system": {
            "name": "ERP Builder",
            "version": "V3",
            "domain": "PET 瓶片贸易 ERP",
        },
        "modules": modules,
        "capabilities": caps,
    })


@router.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    """上传文件 —— 返回访问路径"""
    ext = Path(file.filename or "file").suffix or ".bin"
    safe_name = f"{uuid.uuid4().hex}{ext}"
    file_path = UPLOAD_DIR / safe_name
    content = await file.read()
    file_path.write_bytes(content)
    return APIResponse.ok({"filename": file.filename, "path": f"/uploads/{safe_name}", "size": len(content)})
