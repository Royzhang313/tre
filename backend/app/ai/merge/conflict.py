"""ConflictChecker —— 5 种冲突检测"""

import os

from app.shared.capability_registry import CapabilityRegistry
from app.shared.module_registry import ModuleRegistry


class ConflictChecker:
    BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    @staticmethod
    def check(artifacts: list[dict], module_name: str) -> dict:
        results = []
        target_dir = os.path.join(ConflictChecker.BACKEND_ROOT, "app", "modules", module_name)

        for art in artifacts:
            path = art.get("file_path", "")
            art_type = art.get("artifact_type", "")

            # 1. File conflict
            file_path = os.path.join(target_dir, os.path.basename(path))
            if os.path.exists(file_path):
                results.append({
                    "type": "file_exists",
                    "file": file_path,
                    "message": f"文件 {file_path} 已存在",
                    "severity": "warning",
                })

            # 2. Model conflict (class name)
            if art_type in ("create_entity", "extend_entity"):
                payload = art.get("payload", {})
                class_name = payload.get("name", "")
                if class_name:
                    results.append({
                        "type": "model_conflict",
                        "entity": class_name,
                        "message": f"实体 {class_name} 需检查与已有模型冲突",
                        "severity": "info",
                    })

            # 3. Permission conflict
            if art_type == "create_permission":
                payload = art.get("payload", {})
                code = payload.get("code", "") if isinstance(payload, dict) else str(payload)
                results.append({
                    "type": "permission_conflict",
                    "code": code,
                    "message": f"权限 {code} 需人工确认不重复",
                    "severity": "info",
                })

            # 4. Route conflict
            if art_type == "create_router":
                results.append({
                    "type": "route_conflict",
                    "message": f"路由 /api/v1/{module_name}/ 需确认不冲突",
                    "severity": "info",
                })

            # 5. Capability conflict
            if art_type == "create_capability":
                payload = art.get("payload", {})
                cap_name = payload.get("name", "")
                if cap_name and CapabilityRegistry.get(cap_name):
                    results.append({
                        "type": "capability_conflict",
                        "name": cap_name,
                        "message": f"Capability {cap_name} 已存在",
                        "severity": "error",
                    })

        # 6. Module conflict
        if ModuleRegistry.get(module_name):
            results.append({
                "type": "module_conflict",
                "module": module_name,
                "message": f"模块 {module_name} 已注册",
                "severity": "warning",
            })

        errors = [r for r in results if r["severity"] == "error"]
        warnings = [r for r in results if r["severity"] == "warning"]
        return {
            "has_conflicts": len(errors) > 0,
            "errors": errors,
            "warnings": warnings,
            "total_checks": len(results),
        }
