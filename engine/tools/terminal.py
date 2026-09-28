"""
Terminal execution tools for ground-truth automated test running.
"""

import subprocess
import shlex
import sys
from pathlib import Path
from typing import Optional
from engine.state import TestResult

class TerminalTool:
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()

    def run_command(self, command: str, timeout: int = 120) -> TestResult:
        """Execute a shell command and capture deterministic exit code, stdout, and stderr."""
        try:
            # On Windows, run through powershell / cmd
            use_shell = sys.platform == "win32"
            proc = subprocess.run(
                command,
                cwd=str(self.cwd),
                shell=use_shell,
                capture_output=True,
                text=True,
                timeout=timeout,
                encoding="utf-8",
                errors="replace"
            )
            return TestResult(
                command=command,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                passed=(proc.returncode == 0)
            )
        except subprocess.TimeoutExpired as e:
            return TestResult(
                command=command,
                exit_code=124,
                stdout=e.stdout or "",
                stderr="Execution timed out after {timeout} seconds",
                passed=False
            )
        except Exception as e:
            return TestResult(
                command=command,
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                passed=False
            )
