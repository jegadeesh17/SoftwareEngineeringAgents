"""
Workspace tools for file operations.
"""

from pathlib import Path
from typing import List, Optional

class WorkspaceTool:
    def __init__(self, root_dir: Optional[Path] = None):
        self.root_dir = root_dir or Path.cwd()

    def write_file(self, relative_path: str, content: str) -> Path:
        target = self.root_dir / relative_path
        target.parent.mkdir(parents=True, exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(content)
        return target

    def read_file(self, relative_path: str) -> Optional[str]:
        target = self.root_dir / relative_path
        if not target.exists():
            return None
        with open(target, "r", encoding="utf-8") as f:
            return f.read()

    def list_files(self, sub_dir: str = ".") -> List[str]:
        target = self.root_dir / sub_dir
        if not target.exists():
            return []
        return [str(p.relative_to(self.root_dir)) for p in target.rglob("*") if p.is_file()]
