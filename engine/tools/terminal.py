"""
Terminal execution tools for ground-truth automated test running.
"""

import subprocess
from pathlib import Path
from typing import List, Optional, Union
from engine.state import TestResult

class TerminalTool:
    def __init__(self, cwd: Optional[Path] = None):
        self.cwd = cwd or Path.cwd()

    def run_command(self, command: Union[str, List[str]], timeout: int = 120) -> TestResult:
        """Execute a command and capture deterministic exit code, stdout, and stderr.

        A string is run as a shell command line (quoting, &&, pipes); a list is run
        directly as argv with no shell, so arguments are passed through verbatim.
        """
        use_shell = isinstance(command, str)
        display = command if use_shell else subprocess.list2cmdline(command)
        try:
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
                command=display,
                exit_code=proc.returncode,
                stdout=proc.stdout,
                stderr=proc.stderr,
                passed=(proc.returncode == 0)
            )
        except subprocess.TimeoutExpired as e:
            # TimeoutExpired.stdout can be bytes even when text=True
            stdout = e.stdout or ""
            if isinstance(stdout, bytes):
                stdout = stdout.decode("utf-8", errors="replace")
            return TestResult(
                command=display,
                exit_code=124,
                stdout=stdout,
                stderr=f"Execution timed out after {timeout} seconds",
                passed=False
            )
        except Exception as e:
            return TestResult(
                command=display,
                exit_code=1,
                stdout="",
                stderr=f"Execution error: {str(e)}",
                passed=False
            )
