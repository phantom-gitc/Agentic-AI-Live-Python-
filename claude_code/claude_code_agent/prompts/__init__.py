from __future__ import annotations

from pathlib import Path


# Reads the system prompt that controls the agent behavior.
def load_system_prompt() -> str:
    return (Path(__file__).with_name("system_prompt.md")).read_text(encoding="utf-8")
