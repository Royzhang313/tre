"""OCR 识别服务 —— Provider 模式"""
import json, logging, io, re, asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass

logger = logging.getLogger("ocr")


@dataclass
class OCRResult:
    success: bool
    amount: float | None = None
    bank_name: str | None = None
    bank_account: str | None = None
    payer_name: str | None = None
    receiver_name: str | None = None
    date: str | None = None
    remark: str | None = None
    summary: str | None = None
    raw_text: str | None = None


class BaseOCRProvider(ABC):
    @abstractmethod
    async def recognize(self, image_data: bytes, config: dict) -> OCRResult: ...


# ============================================================
# PaddleOCR —— 本地 OCR，百度出品，中文识别最强，无需网络
# ============================================================

class PaddleOCRProvider(BaseOCRProvider):
    """PaddleOCR —— 百度出品，中文识别精度最高，GPU 加速"""

    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        try:
            from PIL import Image as PILImage

            img = PILImage.open(io.BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            def _run():
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(lang="ch", use_gpu=False, show_log=False)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                results = ocr.ocr(buf.getvalue(), cls=False)
                lines: list[str] = []
                if results and results[0]:
                    for line_info in results[0]:
                        text = line_info[1][0]
                        lines.append(text)
                return "\n".join(lines)

            raw = await asyncio.to_thread(_run)
            logger.info(f"PaddleOCR: {len(raw.split(chr(10)))} 行文字")
            parsed = self._parse_lines(raw.split("\n"))
            return OCRResult(success=True, amount=parsed.get("amount"),
                bank_name=parsed.get("bank_name"), bank_account=parsed.get("bank_account"),
                payer_name=parsed.get("payer_name"), receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"), remark=parsed.get("remark"),
                summary=parsed.get("summary"), raw_text=raw)

        except Exception as e:
            import traceback
            logger.error(f"PaddleOCR [{type(e).__name__}]: {e}\n{traceback.format_exc()}")
            return OCRResult(success=False, remark=f"{type(e).__name__}: {e}" if str(e) else type(e).__name__)

    @staticmethod
    def _parse_lines(lines: list[str]) -> dict:
        parsed: dict = {}
        # 金额
        for t in lines:
            m = re.search(r'(?:CNY|RMB)\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t, re.IGNORECASE)
            if not m: m = re.search(r'(?:金额|小写)[^¥￥]*(?:CNY|RMB)?\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t, re.IGNORECASE)
            if not m: m = re.search(r'(?:金额|小写)[：:\s]*[¥￥]?\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t)
            if not m: m = re.search(r'[¥￥]\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t)
            if not m: m = re.search(r'([\d,]{1,3}(?:,\d{3})*(?:\.\d{2}))', t)
            if m:
                try: parsed["amount"] = float(re.sub(r'[\s，,]', '', m.group(1)).replace("..", "."))
                except ValueError: pass
                break
        # 银行
        for t in lines:
            m = re.search(r'(招商银行|中国工商银行|中国建设银行|中国银行|中国农业银行|浦发银行|交通银行|中信银行|兴业银行|民生银行|光大银行|华夏银行|广发银行|平安银行|北京银行|上海银行|\S+银行)', t)
            if m: parsed["bank_name"] = m.group(1); break
        # 付款账号
        for t in lines:
            if "付款账号" in t or "付款账户" in t:
                parts = re.split(r'[：:]', t, maxsplit=1)
                if len(parts) > 1: parsed["bank_account"] = parts[-1].strip()
                break
        if not parsed.get("bank_account"):
            for t in lines:
                m = re.search(r'账号[：:]\s*(\d{10,25})', t)
                if m: parsed["bank_account"] = m.group(1); break
        # 付款人
        for t in lines:
            if "付款人" in t or "付款方" in t:
                parts = re.split(r'[：:]', t, maxsplit=1)
                if len(parts) > 1: parsed["payer_name"] = parts[-1].strip()
                break
        # 收款人
        for t in lines:
            if "收款人" in t or "收款方" in t:
                parts = re.split(r'[：:]', t, maxsplit=1)
                if len(parts) > 1: parsed["receiver_name"] = parts[-1].strip()
                break
        # 日期
        for t in lines:
            m = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', t)
            if m:
                parsed["date"] = m.group(1).replace("年", "-").replace("月", "-").replace("日", "")
                break
        # 摘要
        for t in lines:
            if "摘要" in t or "用途" in t:
                parts = re.split(r'[：:]', t, maxsplit=1)
                if len(parts) > 1: parsed["summary"] = parts[-1].strip()
                break
        return parsed


class SmartOCRProvider(BaseOCRProvider):
    """PaddleOCR 取文字 + LLM 结构化提取 —— 适配各种截图格式"""

    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        import base64, httpx

        # Step 1: PaddleOCR 取原始文字
        try:
            from PIL import Image as PILImage
            img = PILImage.open(io.BytesIO(image_data))
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")

            def _run_paddle():
                from paddleocr import PaddleOCR
                ocr = PaddleOCR(lang="ch", use_gpu=False, show_log=False)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                results = ocr.ocr(buf.getvalue(), cls=False)
                lines: list[str] = []
                if results and results[0]:
                    for line_info in results[0]:
                        text = line_info[1][0]
                        lines.append(text)
                return "\n".join(lines)

            raw_text = await asyncio.to_thread(_run_paddle)
            logger.info(f"SmartOCR Paddle: {len(raw_text.split(chr(10)))} 行文字")
        except Exception as e:
            raw_text = ""
            logger.warning(f"PaddleOCR 失败，降级为纯 LLM 识别: {e}")

        # Step 2: LLM 结构化提取
        api_key = config.get("ocr_api_key", "") or config.get("deepseek_api_key", "")
        if not api_key:
            # 无 API Key 时回退到 PaddleOCR 正则提取
            logger.warning("SmartOCR 无 DeepSeek API Key，回退正则提取")
            parsed = PaddleOCRProvider._parse_lines(raw_text.split("\n") if raw_text else [])
            return OCRResult(success=True, amount=parsed.get("amount"),
                bank_name=parsed.get("bank_name"), bank_account=parsed.get("bank_account"),
                payer_name=parsed.get("payer_name"), receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"), remark=parsed.get("remark"),
                summary=parsed.get("summary"), raw_text=raw_text)

        try:
            prompt = f"""请从以下银行转账回单/支付凭证的OCR文字中提取关键信息，以JSON格式返回。只返回JSON，不要其他文字。

如果某项识别不到，值设为null。金额只返回数字，去掉货币符号和逗号。

{{
  "amount": 金额(数字，取小写金额),
  "bank_name": "银行名称（付款开户行）",
  "bank_account": "付款账号",
  "payer_name": "付款人户名/名称",
  "receiver_name": "收款人户名/名称",
  "receiver_bank": "收款开户行",
  "receiver_account": "收款账号",
  "date": "交易日期(YYYY-MM-DD)",
  "summary": "用途/摘要",
  "remark": "其他备注"
}}

OCR文字内容：
{raw_text[:3000]}"""

            api_url = config.get("ocr_api_url", "") or config.get("deepseek_base_url", "https://api.deepseek.com/v1") + "/chat/completions"
            model = config.get("ocr_api_secret", "") or config.get("default_ai_model", "deepseek-chat")

            body = {
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 500,
                "temperature": 0.1,
            }
            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.post(api_url.rstrip("/") + "/chat/completions" if not api_url.endswith("/chat/completions") else api_url,
                    json=body, headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
                r.raise_for_status()
                result = r.json()

            content = result["choices"][0]["message"]["content"]
            for tag in ("```json", "```"):
                if tag in content:
                    content = content.split(tag)[1].split("```")[0].strip()

            parsed = json.loads(content)
            amt = parsed.get("amount")

            return OCRResult(
                success=True,
                amount=float(amt) if amt else None,
                bank_name=parsed.get("bank_name"),
                bank_account=parsed.get("bank_account") or parsed.get("receiver_account"),
                payer_name=parsed.get("payer_name"),
                receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"),
                remark=parsed.get("remark"),
                summary=parsed.get("summary"),
                raw_text=raw_text,
            )

        except Exception as e:
            import traceback
            logger.error(f"SmartOCR LLM 失败: {e}\n{traceback.format_exc()}")
            # 回退正则
            parsed = PaddleOCRProvider._parse_lines(raw_text.split("\n") if raw_text else [])
            return OCRResult(success=True, amount=parsed.get("amount"),
                bank_name=parsed.get("bank_name"), bank_account=parsed.get("bank_account"),
                payer_name=parsed.get("payer_name"), receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"), remark=parsed.get("remark"),
                summary=parsed.get("summary"), raw_text=raw_text)


class AliyunOCRProvider(BaseOCRProvider):
    """Tesseract OCR —— 本地，中文支持，30MB安装，立即可用"""

    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        import asyncio
        try:
            # PIL 预处理：灰度 + 放大（提升 Tesseract 中文识别率）
            processed = image_data
            try:
                from PIL import Image  # type: ignore[import-not-found]
                img = Image.open(io.BytesIO(image_data))  # type: ignore[assignment]
                if img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")
                img = img.convert("L")
                if img.width < 1500:
                    ratio = 2000 / img.width
                    img = img.resize((2000, int(img.height * ratio)), Image.LANCZOS)
                buf = io.BytesIO()
                img.save(buf, format="PNG")
                processed = buf.getvalue()
            except Exception:
                pass

            def _run():
                import pytesseract
                from PIL import Image as PILImage
                img = PILImage.open(io.BytesIO(processed))
                return pytesseract.image_to_string(img, lang='chi_sim+eng')

            raw = await asyncio.to_thread(_run)
            lines = [l.strip() for l in raw.split('\n') if l.strip()]
            logger.error(f"Tesseract: {len(lines)} 行文字")

            # 正则提取
            parsed: dict = {}
            # 金额（支持空格、中文逗号等格式）
            for t in lines:
                m = re.search(r'(?:CNY|RMB)\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t, re.IGNORECASE)
                if not m: m = re.search(r'(?:金额|小写)[^¥￥]*(?:CNY|RMB)?\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t, re.IGNORECASE)
                if not m: m = re.search(r'(?:金额|小写)[：:\s]*[¥￥]?\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t)
                if not m: m = re.search(r'[¥￥]\s*"?\s*([\d,\s，]+\.[\d\s]{2,3})', t)
                if not m: m = re.search(r'([\d,]{1,3}(?:,\d{3})*(?:\.\d{2}))', t)
                if m:
                    try: parsed["amount"] = float(re.sub(r'[\s，,]', '', m.group(1)).replace("..","."))
                    except ValueError: pass
                    break
            # 银行
            for t in lines:
                m = re.search(r'(招商银行|中国工商银行|中国建设银行|中国银行|中国农业银行|浦发银行|交通银行|中信银行|兴业银行|民生银行|光大银行|华夏银行|广发银行|平安银行|北京银行|上海银行|\S+银行)', t)
                if m: parsed["bank_name"] = m.group(1); break
            # 付款账号
            for t in lines:
                if "付款账号" in t or "付款账户" in t:
                    parts = re.split(r'[：:]', t, maxsplit=1)
                    if len(parts) > 1: parsed["bank_account"] = parts[-1].strip()
                    break
            if not parsed.get("bank_account"):
                for t in lines:
                    m = re.search(r'账号[：:]\s*(\d{10,25})', t)
                    if m: parsed["bank_account"] = m.group(1); break
            # 付款人
            for t in lines:
                if "付款人" in t or "付款方" in t:
                    parts = re.split(r'[：:]', t, maxsplit=1)
                    if len(parts) > 1: parsed["payer_name"] = parts[-1].strip()
                    break
            # 收款人
            for t in lines:
                if "收款人" in t or "收款方" in t:
                    parts = re.split(r'[：:]', t, maxsplit=1)
                    if len(parts) > 1: parsed["receiver_name"] = parts[-1].strip()
                    break
            # 日期
            for t in lines:
                m = re.search(r'(\d{4}[-/年]\d{1,2}[-/月]\d{1,2})', t)
                if m:
                    parsed["date"] = m.group(1).replace("年","-").replace("月","-").replace("日","")
                    break
            # 摘要/用途 —— 仅做结构化提取，不写入备注
            for t in lines:
                if "摘要" in t or "用途" in t:
                    parts = re.split(r'[：:]', t, maxsplit=1)
                    if len(parts) > 1: parsed["summary"] = parts[-1].strip()
                    break

            return OCRResult(success=True, amount=parsed.get("amount"),
                bank_name=parsed.get("bank_name"), bank_account=parsed.get("bank_account"),
                payer_name=parsed.get("payer_name"), receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"), remark=parsed.get("remark"),
                summary=parsed.get("summary"), raw_text=raw)

        except Exception as e:
            import traceback
            logger.error(f"OCR [{type(e).__name__}]: {e}\n{traceback.format_exc()}")
            return OCRResult(success=False, remark=f"{type(e).__name__}: {e}" if str(e) else type(e).__name__)


class DeepSeekProvider(BaseOCRProvider):
    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        import base64, httpx
        api_key = config.get("ocr_api_key", "")
        api_url = config.get("ocr_api_url", "") or "https://api.deepseek.com/chat/completions"
        if not api_key: return OCRResult(success=False, remark="DeepSeek API Key 未配置")
        try:
            img_b64 = base64.b64encode(image_data).decode()
            body = {"model": config.get("ocr_api_secret","") or "deepseek-chat",
                "messages":[{"role":"user","content":[
                    {"type":"text","text":"请识别这张银行回单图片，提取以下信息并以JSON格式返回。只返回JSON，不要其他文字。\n{\n  \"amount\": 金额(数字),\n  \"bank_name\": \"银行名称\",\n  \"bank_account\": \"银行账号\",\n  \"payer_name\": \"付款方名称\",\n  \"receiver_name\": \"收款方名称\",\n  \"date\": \"交易日期(YYYY-MM-DD)\",\n  \"remark\": \"摘要/备注\"\n}\n如果某项识别不到，值设为null。"},
                    {"type":"image_url","image_url":{"url":f"data:image/jpeg;base64,{img_b64}"}}]}],
                "max_tokens":1000,"temperature":0.1}
            async with httpx.AsyncClient(timeout=60) as c:
                r = await c.post(api_url, json=body, headers={"Authorization":f"Bearer {api_key}","Content-Type":"application/json"})
                r.raise_for_status(); result = r.json()
            content = result["choices"][0]["message"]["content"]
            for tag in ("```json","```"):
                if tag in content: content = content.split(tag)[1].split("```")[0]
            parsed = json.loads(content.strip()); amt = parsed.get("amount")
            return OCRResult(success=True, amount=float(amt) if amt else None,
                bank_name=parsed.get("bank_name"), bank_account=parsed.get("bank_account"),
                payer_name=parsed.get("payer_name"), receiver_name=parsed.get("receiver_name"),
                date=parsed.get("date"), remark=parsed.get("remark"), raw_text=content)
        except Exception as e:
            return OCRResult(success=False, remark=str(e)[:500])


class BaiduOCRProvider(BaseOCRProvider):
    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        import base64, httpx
        ak = config.get("ocr_api_key",""); sk = config.get("ocr_api_secret","")
        if not ak or not sk: return OCRResult(success=False, remark="百度 OCR 未配置")
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                tr = await c.post("https://aip.baidubce.com/oauth/2.0/token",
                    params={"grant_type":"client_credentials","client_id":ak,"client_secret":sk})
                tr.raise_for_status(); token = tr.json().get("access_token")
                if not token: return OCRResult(success=False, remark="百度 Token 获取失败")
                rr = await c.post("https://aip.baidubce.com/rest/2.0/ocr/v1/receipt",
                    data={"image":base64.b64encode(image_data).decode(),"access_token":token})
                rr.raise_for_status(); result = rr.json()
            w = result.get("words_result",{})
            return OCRResult(success=True, amount=float(w["金额"]) if w.get("金额") else None,
                bank_name=w.get("银行名称") or w.get("付款银行"),
                bank_account=w.get("银行账号") or w.get("付款账号"),
                payer_name=w.get("付款方") or w.get("付款人"),
                receiver_name=w.get("收款方") or w.get("收款人"),
                date=w.get("日期") or w.get("交易日期"),
                remark=w.get("摘要") or w.get("备注"), raw_text=json.dumps(w,ensure_ascii=False))
        except Exception as e:
            return OCRResult(success=False, remark=str(e)[:500])


class MockOCRProvider(BaseOCRProvider):
    async def recognize(self, image_data: bytes, config: dict) -> OCRResult:
        return OCRResult(success=True, amount=500000.00, bank_name="中国工商银行",
            bank_account="6222021234567890123", payer_name="某贸易有限公司",
            date="2026-07-09", remark="货款", raw_text="模拟识别结果")


PROVIDERS = {
    "smart": SmartOCRProvider(),
    "aliyun": AliyunOCRProvider(),
    "paddleocr": PaddleOCRProvider(),
    "deepseek": DeepSeekProvider(),
    "baidu": BaiduOCRProvider(),
    "mock": MockOCRProvider(),
}


async def ocr_recognize(image_data: bytes, session_factory=None) -> OCRResult:
    if session_factory:
        async with session_factory() as session:
            from sqlalchemy import select
            from app.modules.system.models import SysConfig
            r = await session.execute(select(SysConfig))
            rows = r.fetchall()
            config = {}
            for row in rows:
                item = row[0]
                if item is not None:
                    config[item.key] = item.value
    else:
        config = {}
    enabled = config.get("ocr_enabled", "false")
    if enabled != "true":
        return OCRResult(success=False, remark="OCR 功能未启用")
    provider_key = config.get("ocr_provider", "aliyun")
    provider = PROVIDERS.get(provider_key, MockOCRProvider())
    return await provider.recognize(image_data, config)
