from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.live import Live
from rich.table import Table

from .ai.client import AIClient
from .config import Settings
from .prompts import load_system_prompt
from .tools import ToolBox, ToolError


class CodingAgentError(RuntimeError):
    """Raised when the coding agent cannot continue."""


@dataclass(frozen=True)
class AgentResult:
    ok: bool
    summary: str


class CodingAgent:
    # Sets up the AI client, prompt, tools, and workspace for one agent session.
    def __init__(
        self,
        settings: Settings,
        workspace: Path,
        console: Console,
        verbose: bool = False,
    ) -> None:
        self.workspace = workspace.resolve()
        if not self.workspace.exists() or not self.workspace.is_dir():
            raise CodingAgentError(f"Workspace does not exist: {self.workspace}")

        self.console = console
        self.verbose = verbose
        self.client = AIClient(settings)
        self.tools = ToolBox(self.workspace)
        self.system_prompt = load_system_prompt()

    # Runs the task loop where the AI chooses tools until the job is finished.
    def run(self, task: str, max_steps: int = 12) -> AgentResult:
        messages: list[dict[str, str]] = [
            {"role": "system", "content": self.system_prompt},
            {
                "role": "user",
                "content": self._initial_user_message(task),
            },
        ]
        events: list[str] = ["Task received"]
        files_changed: set[str] = set()

        with Live(self._status_table(task, events, files_changed), console=self.console, refresh_per_second=6) as live:
            for step in range(1, max_steps + 1):
                events.append(f"Step {step}: asking AI")
                live.update(self._status_table(task, events, files_changed))

                response = self.client.complete(messages)
                action = self._parse_action(response)

                if self.verbose:
                    self.console.print_json(data=action)

                action_name = action.get("action")
                args = action.get("args") or {}

                if action_name == "finish":
                    summary = str(args.get("summary") or "Task completed.")
                    return AgentResult(ok=True, summary=summary)

                if action_name == "ask_user":
                    question = str(args.get("question") or "More information is required.")
                    return AgentResult(ok=False, summary=f"Need input: {question}")

                events.append(f"Running tool: {action_name}")
                live.update(self._status_table(task, events, files_changed))

                tool_result = self._run_tool(action_name, args)
                if action_name in {"write_file", "append_file"} and tool_result.get("ok"):
                    files_changed.add(str(args.get("path", "")))

                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {
                        "role": "user",
                        "content": "Tool result:\n"
                        + json.dumps(tool_result, ensure_ascii=True, indent=2)
                        + "\nChoose the next JSON action.",
                    }
                )
                events.append("Tool completed" if tool_result.get("ok") else "Tool failed")
                live.update(self._status_table(task, events, files_changed))

        return AgentResult(
            ok=False,
            summary=f"Stopped after {max_steps} steps. Increase --max-steps or narrow the task.",
        )

    # Calls the matching local tool requested by the AI.
    def _run_tool(self, action_name: str, args: dict[str, Any]) -> dict[str, Any]:
        try:
            if action_name == "list_files":
                return self.tools.list_files(**args)
            if action_name == "read_file":
                return self.tools.read_file(**args)
            if action_name == "write_file":
                return self.tools.write_file(**args)
            if action_name == "append_file":
                return self.tools.append_file(**args)
            if action_name == "run_command":
                return self.tools.run_command(**args)
        except TypeError as exc:
            return {"ok": False, "error": f"Invalid tool arguments: {exc}"}
        except ToolError as exc:
            return {"ok": False, "error": str(exc)}

        return {"ok": False, "error": f"Unknown action: {action_name}"}

    # Converts the AI response text into a Python dictionary action.
    def _parse_action(self, response: str) -> dict[str, Any]:
        text = self._extract_json_text(response)
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise CodingAgentError(f"AI returned invalid JSON: {exc}\n\n{text}") from exc
        if not isinstance(parsed, dict):
            raise CodingAgentError("AI response must be a JSON object.")
        return parsed

    # Pulls out the JSON object when the model adds code fences or extra text.
    def _extract_json_text(self, response: str) -> str:
        text = response.strip()
        if text.startswith("```"):
            text = text.strip("`")
            if text.startswith("json"):
                text = text[4:].strip()
        if text.startswith("{") and text.endswith("}"):
            return text

        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return text
        return text[start : end + 1]

    # Builds the first user message with the task and workspace context.
    def _initial_user_message(self, task: str) -> str:
        return (
            f"Workspace: {self.workspace}\n"
            f"Task: {task}\n\n"
            "Start by inspecting the project. Use only the documented JSON action protocol."
        )

    @staticmethod
    # Builds the small live status table shown while the agent works.
    def _status_table(task: str, events: list[str], files_changed: set[str]) -> Table:
        table = Table.grid(padding=(0, 1))
        table.add_column(style="cyan", no_wrap=True)
        table.add_column()
        table.add_row("Task", task[:90])
        table.add_row("Status", events[-1] if events else "Idle")
        if files_changed:
            table.add_row("Changed", ", ".join(sorted(files_changed))[:90])
        recent = "\n".join(f"- {event}" for event in events[-5:])
        table.add_row("Progress", recent)
        return table
