"""Workflow planning and execution helpers for multi-step tasks."""

from __future__ import annotations

from dataclasses import dataclass, field
import re

from .router import FILE_PATTERN
from .state import AgentState
from .tools import ToolResult


@dataclass(frozen=True)
class WorkflowStep:
    """One planned step inside a multi-step workflow."""

    title: str                      # 步骤标题
    kind: str                       # tool 或 synthesize
    tool_name: str | None = None    # 工具名
    tool_input: str | None = None   # 工具输入
    note: str = ""                  # 步骤说明


@dataclass(frozen=True)
class WorkflowPlan:
    """A simple sequential workflow plan."""

    objective: str  # 工作流目标
    steps: list[WorkflowStep] = field(default_factory=list)  # 顺序步骤

    @property
    def is_multi_step(self) -> bool:
        """Return True when the plan contains more than one executable step."""

        return len(self.steps) > 1

    def describe(self) -> str:
        """Render the workflow into a compact summary string."""

        parts = [self.objective]
        for index, step in enumerate(self.steps, start=1):
            if step.kind == "tool":
                parts.append(f"{index}. {step.kind}:{step.tool_name}:{step.tool_input}")
            else:
                parts.append(f"{index}. {step.kind}:{step.note}")
        return " | ".join(parts)

    def to_dict(self) -> dict[str, object]:
        """Convert the workflow plan into JSON-ready data."""

        return {
            "objective": self.objective,
            "steps": [
                {
                    "title": step.title,
                    "kind": step.kind,
                    "tool_name": step.tool_name,
                    "tool_input": step.tool_input,
                    "note": step.note,
                }
                for step in self.steps
            ],
        }


WORKFLOW_MARKERS = [
    " and then ",
    " then ",
    " after that ",
    " first ",
    " next ",
    "step by step",
    "workflow",
    "multiple steps",
]


def _find_primary_path(text: str) -> str | None:
    """Extract the first file path mentioned by the user."""

    match = FILE_PATTERN.search(text)
    return match.group("path") if match else None


def _looks_like_workflow_request(text: str) -> bool:
    """Return True when the request appears to contain ordered actions."""

    lowered = f" {text.lower()} "
    return any(marker in lowered for marker in WORKFLOW_MARKERS)


def build_workflow_plan(user_input: str) -> WorkflowPlan:
    """Build a small sequential plan from the user input.

    The planner is intentionally rule-based for now so the state and execution
    chain stay easy to understand and later replace with a smarter planner.
    """

    text = user_input.strip()
    lowered = text.lower()
    path = _find_primary_path(text) or "README.md"
    steps: list[WorkflowStep] = []

    # 场景1：用户要求先读文件，再做统计或摘要
    if ("read" in lowered or "inspect" in lowered or "summarize" in lowered or "summarise" in lowered) and path:
        steps.append(
            WorkflowStep(
                title="Read source file",
                kind="tool",
                tool_name="read_file",
                tool_input=path,
                note="Load the file before the next step.",
            )
        )

    # 场景2：用户明确要求统计行数
    if "count lines" in lowered or "line count" in lowered or "number of lines" in lowered:
        steps.append(
            WorkflowStep(
                title="Count lines",
                kind="tool",
                tool_name="count_lines",
                tool_input=path,
                note="Count lines after the file has been selected.",
            )
        )

    # 场景3：用户要求先看目录，再读文件
    if ("directory" in lowered or "directories" in lowered or "folder" in lowered) and ("read" in lowered or "inspect" in lowered):
        steps.insert(
            0,
            WorkflowStep(
                title="Inspect directories",
                kind="tool",
                tool_name="list_dir",
                tool_input=".",
                note="Inspect the workspace before reading a file.",
            ),
        )

    # 如果没有形成真正的多步流程，但用户用了顺序型表达，也给一个两步计划
    if not steps and _looks_like_workflow_request(text):
        steps = [
            WorkflowStep(
                title="Inspect workspace",
                kind="tool",
                tool_name="list_dir",
                tool_input=".",
                note="Inspect the workspace first.",
            ),
            WorkflowStep(
                title="Summarize request",
                kind="synthesize",
                note="Combine the inspection result into a short answer.",
            ),
        ]

    # 工作流至少应该有两步，才能真正体现“先做一件事，再做下一件事”
    if len(steps) == 1:
        steps.append(
            WorkflowStep(
                title="Synthesize answer",
                kind="synthesize",
                note="Use the tool result to answer the request.",
            )
        )

    return WorkflowPlan(objective=text, steps=steps)


def build_workflow_summary(state: AgentState, plan: WorkflowPlan) -> str:
    """Create a user-facing answer from workflow execution results."""

    return build_workflow_summary_from_results(plan, state.tool_results, state.workflow_summary)


def build_workflow_summary_from_results(
    plan: WorkflowPlan,
    tool_results: list[ToolResult],
    workflow_summary: str = "",
) -> str:
    """Create a user-facing answer from workflow results without AgentState."""

    parts: list[str] = [f"Result: workflow completed for '{plan.objective}'."]
    for result in tool_results:
        if result.tool_name == "read_file":
            parts.append(f"Read file: {result.output.splitlines()[0]}")
            parts.append(f"Summary:\n{_summarize_tool_text(result.output)}")
        elif result.tool_name == "list_dir":
            parts.append(f"Directory inspection:\n{result.output}")
        elif result.tool_name == "count_lines":
            parts.append(result.output)
    if workflow_summary:
        parts.append(f"Workflow summary: {workflow_summary}")
    return "\n\n".join(parts)


def _summarize_tool_text(text: str, limit: int = 12) -> str:
    """Create a short deterministic summary from a tool result."""

    lines = text.splitlines()
    head = lines[:limit]
    if len(lines) > limit:
        head.append("... (truncated)")
    return "\n".join(head)
