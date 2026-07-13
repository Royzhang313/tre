"""MergeApplier —— 写入文件 + 注册 + 备份"""

import json
import os


class MergeApplier:
    BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    @staticmethod
    def apply(artifacts: list[dict], module_name: str) -> dict:
        target_dir = os.path.join(MergeApplier.BACKEND_ROOT, "app", "modules", module_name)
        os.makedirs(target_dir, exist_ok=True)

        applied = []
        backup = {}

        for art in artifacts:
            path = art.get("file_path", "")
            content = art.get("content", "")
            file_name = os.path.basename(path)
            target_path = os.path.join(target_dir, file_name)

            # 备份
            if os.path.exists(target_path):
                with open(target_path) as f:
                    backup[target_path] = f.read()

            # 写入
            with open(target_path, "w") as f:
                f.write(content)

            applied.append({"path": target_path, "size": len(content)})

        # 保存备份快照
        snapshot_path = os.path.join(target_dir, ".merge_snapshot.json")
        with open(snapshot_path, "w") as f:
            json.dump({"backup": {k: len(v) for k, v in backup.items()}, "files": applied}, f)

        return {"applied": len(applied), "files": applied, "snapshot": snapshot_path}

    @staticmethod
    def rollback(module_name: str) -> dict:
        """从快照回滚"""
        target_dir = os.path.join(MergeApplier.BACKEND_ROOT, "app", "modules", module_name)
        snapshot_path = os.path.join(target_dir, ".merge_snapshot.json")

        if not os.path.exists(snapshot_path):
            return {"status": "no_snapshot"}

        rolled_back = []
        for file_name in os.listdir(target_dir):
            if file_name.endswith(".py") and file_name != "__init__.py":
                file_path = os.path.join(target_dir, file_name)
                os.remove(file_path)
                rolled_back.append(file_path)

        os.remove(snapshot_path)
        return {"status": "rolled_back", "files": rolled_back}
