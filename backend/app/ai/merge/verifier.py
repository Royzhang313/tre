"""MergeVerifier —— 自动执行 ruff + mypy"""

import os
import subprocess


class MergeVerifier:
    BACKEND_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "..")

    @staticmethod
    def verify() -> dict:
        results = {}

        # ruff
        try:
            ruff_result = subprocess.run(
                ["ruff", "check", "app/"], cwd=MergeVerifier.BACKEND_ROOT,
                capture_output=True, text=True, timeout=30,
            )
            results["ruff"] = {"passed": ruff_result.returncode == 0, "output": ruff_result.stdout[:500]}
        except Exception as e:
            results["ruff"] = {"passed": False, "error": str(e)}

        # mypy
        try:
            mypy_result = subprocess.run(
                ["mypy", "app/", "--ignore-missing-imports"], cwd=MergeVerifier.BACKEND_ROOT,
                capture_output=True, text=True, timeout=60,
            )
            results["mypy"] = {"passed": mypy_result.returncode == 0, "output": mypy_result.stdout[:500]}
        except Exception as e:
            results["mypy"] = {"passed": False, "error": str(e)}

        all_pass = results.get("ruff", {}).get("passed", False) and results.get("mypy", {}).get("passed", False)
        return {"all_pass": all_pass, "checks": results}
