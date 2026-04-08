from __future__ import annotations

import subprocess
from pathlib import Path
from .models import TestRunResult

class TestRunner:
    def __init__(self, project_root):
        self.project_root = Path(project_root).resolve()
    
    def write_test_file(self,relative_path , code):
        file_path = self.project_root / relative_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(code, encoding="utf-8")
        return file_path
    
    def run_pytest_file(self, relative_path: str) -> TestRunResult:
        file_path = self.project_root / relative_path

        result = subprocess.run(
            ["pytest", str(file_path)],
            cwd=self.project_root,
            capture_output=True,
            text=True,
        )
        print(result.stdout)

        return TestRunResult(
            passed=result.returncode == 0,
            exit_code=result.returncode,
            test_file_path=str(file_path),
            stdout=result.stdout,
            stderr=result.stderr,
        )
    def write_and_run(self, relative_path: str, code: str) -> TestRunResult:
        self.write_test_file(relative_path, code)
        return self.run_pytest_file(relative_path)
    