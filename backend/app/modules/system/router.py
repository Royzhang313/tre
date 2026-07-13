"""系统配置 —— Router"""

from uuid import UUID

from fastapi import APIRouter, File, UploadFile

from app.core.database import async_session_factory
from app.modules.system.models import SysConfig
from app.modules.system.schemas import SysConfigBatchUpdate, SysConfigUpdate
from app.shared.base_schema import APIResponse
from app.shared.orm_utils import orm_to_dict as _to_dict
from app.shared.ocr_service import ocr_recognize
from app.shared.orm_utils import orm_to_dict as _to_dict

router = APIRouter(prefix="/system", tags=["系统配置"])




@router.get("/configs")
async def list_configs():
    """获取所有系统配置"""
    async with async_session_factory() as session:
        from sqlalchemy import select
        r = await session.execute(select(SysConfig))
        items = r.scalars().all()
    return APIResponse.ok({_to_dict(item)["key"]: _to_dict(item)["value"] for item in items})


@router.get("/configs/{key}")
async def get_config(key: str):
    """获取单个配置"""
    async with async_session_factory() as session:
        from sqlalchemy import select
        r = await session.execute(select(SysConfig).where(SysConfig.key == key))
        item = r.scalar_one_or_none()
    return APIResponse.ok({key: _to_dict(item)["value"] if item else None})


@router.put("/configs")
async def batch_update_configs(body: SysConfigBatchUpdate):
    """批量更新配置"""
    async with async_session_factory() as session:
        from sqlalchemy import select
        for key, value in body.configs.items():
            r = await session.execute(select(SysConfig).where(SysConfig.key == key))
            existing = r.scalar_one_or_none()
            if existing:
                existing.value = value
            else:
                session.add(SysConfig(key=key, value=value))
        await session.commit()
    return APIResponse.ok(None, message="配置已保存")


@router.put("/configs/{key}")
async def update_config(key: str, body: SysConfigUpdate):
    """更新单个配置"""
    async with async_session_factory() as session:
        from sqlalchemy import select
        r = await session.execute(select(SysConfig).where(SysConfig.key == key))
        existing = r.scalar_one_or_none()
        if existing:
            existing.value = body.value
            existing.description = body.description
        else:
            session.add(SysConfig(key=key, value=body.value, description=body.description))
        await session.commit()
    return APIResponse.ok(None, message="已保存")


@router.post("/ocr/recognize")
async def ocr_recognize_upload(file: UploadFile = File(...)):
    """上传银行回单图片进行 OCR 识别"""
    image_data = await file.read()
    result = await ocr_recognize(image_data, async_session_factory)
    return APIResponse.ok({
        "success": result.success,
        "amount": result.amount,
        "bank_name": result.bank_name,
        "bank_account": result.bank_account,
        "payer_name": result.payer_name,
        "receiver_name": result.receiver_name,
        "date": result.date,
        "remark": result.remark,
        "summary": result.summary,
        "raw_text": result.raw_text,
    })
