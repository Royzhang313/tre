"""DiffGenerator —— 文件级变更预览"""


class DiffGenerator:
    @staticmethod
    def generate(artifacts: list[dict], module_name: str) -> dict:
        files = []
        for art in artifacts:
            path = art.get("file_path", "")
            content = art.get("content", "")
            art_type = art.get("artifact_type", "")
            files.append({
                "path": path,
                "artifact_type": art_type,
                "action": "create" if "create_" in art_type else "modify",
                "size_bytes": len(content),
                "preview": content[:500],
            })
        return {
            "module": module_name,
            "total_files": len(files),
            "new_files": [f for f in files if f["action"] == "create"],
            "modified_files": [f for f in files if f["action"] == "modify"],
            "files": files,
        }
