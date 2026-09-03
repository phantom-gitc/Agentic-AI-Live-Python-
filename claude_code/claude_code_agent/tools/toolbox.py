from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any


class ToolError(RuntimeError):
    """Raised when a requested local tool action is unsafe or invalid."""


class ToolBox:
    # Stores the workspace folder that all tools must stay inside.
    def __init__(self, workspace: Path) -> None:
        self.workspace = workspace.resolve()

    # Lists files and folders so the AI can inspect the project.
    def list_files(self, path: str = ".", max_depth: int = 2) -> dict[str, Any]:
        root = self._resolve(path)
        if not root.exists():
            raise ToolError(f"Path does not exist: {path}")
        if not root.is_dir():
            raise ToolError(f"Path is not a directory: {path}")

        rows: list[str] = []
        base_depth = len(root.parts)
        for current, dirs, files in os.walk(root):
            current_path = Path(current)
            depth = len(current_path.parts) - base_depth
            dirs[:] = sorted(
                d for d in dirs if d not in {".git", "__pycache__", ".pytest_cache", "venv", ".venv", "node_modules"}
            )
            if depth >= max_depth:
                dirs[:] = []
            indent = "  " * depth
            if current_path != root:
                rows.append(f"{indent}{current_path.name}/")
            for file_name in sorted(files):
                rows.append(f"{indent}  {file_name}")
        return {"ok": True, "path": str(root.relative_to(self.workspace)), "files": rows[:300]}

    # Reads a text file and returns a safe amount of its content.
    def read_file(self, path: str, max_chars: int = 12000) -> dict[str, Any]:
        file_path = self._resolve(path)
        if not file_path.exists():
            raise ToolError(f"File does not exist: {path}")
        if not file_path.is_file():
            raise ToolError(f"Path is not a file: {path}")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return {
            "ok": True,
            "path": str(file_path.relative_to(self.workspace)),
            "content": content[:max_chars],
            "truncated": len(content) > max_chars,
        }

    # Writes a complete file inside the workspace.
    def write_file(self, path: str, content: str) -> dict[str, Any]:
        file_path = self._resolve(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        file_path.write_text(content, encoding="utf-8")
        return {"ok": True, "path": str(file_path.relative_to(self.workspace)), "bytes": len(content.encode("utf-8"))}

    # Adds text to the end of a file inside the workspace.
    def append_file(self, path: str, content: str) -> dict[str, Any]:
        file_path = self._resolve(path)
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with file_path.open("a", encoding="utf-8") as handle:
            handle.write(content)
        return {"ok": True, "path": str(file_path.relative_to(self.workspace)), "bytes": len(content.encode("utf-8"))}

    # Runs a safe shell command from the workspace and captures the output.
    def run_command(self, command: str, timeout_seconds: int = 60) -> dict[str, Any]:
        self._validate_command(command)
        completed = subprocess.run(
            command,
            cwd=self.workspace,
            shell=True,
            text=True,
            capture_output=True,
            timeout=timeout_seconds,
        )
        return {
            "ok": completed.returncode == 0,
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout[-12000:],
            "stderr": completed.stderr[-12000:],
        }

    # Resolves a requested path and blocks anything outside the workspace.
    def _resolve(self, path: str) -> Path:
        candidate = (self.workspace / path).resolve()
        if candidate == self.workspace or self.workspace in candidate.parents:
            return candidate
        raise ToolError(f"Path escapes workspace: {path}")

    @staticmethod
    # Blocks commands that could delete files or rewrite git history.
    def _validate_command(command: str) -> None:
        lowered = command.lower()
        blocked = [
            " rm ",
            " del ",
            " rmdir ",
            " remove-item",
            "git reset",
            "git checkout",
            "format ",
            "shutdown",
            "reg delete",
        ]
        padded = f" {lowered} "
        if any(token in padded for token in blocked):
            raise ToolError(f"Blocked potentially destructive command: {command}")
