"""Unified recovery models for agent, tool, skill, and graph failures."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class RecoveryPlan:
    """Standard recovery record shared by tool and skill failure paths."""

    status: str  # 恢复计划状态，当前失败恢复路径通常为 failed
    failure_type: str  # 标准失败分类，用于后续选择不同恢复策略
    source_type: str  # 失败来源类型，例如 tool / skill / exception
    source_name: str  # 失败来源名称，例如 read_workspace_file / learning_explanation
    reason: str  # 失败原因，优先保留底层工具或 Skill step 的错误
    next_safe_action: str  # 下一步安全操作建议，不自动执行有风险修复
    tool_name: str | None = None  # 普通工具失败或 Skill step 工具失败时的工具名
    tool_input: dict[str, Any] | None = None  # 工具输入参数
    skill_name: str | None = None  # Skill 失败时的 skill 名称
    failed_step: dict[str, Any] | None = None  # Skill 失败时的步骤信息
    completed_steps: int | None = None  # Skill 失败前已完成步骤数
    metadata: dict[str, Any] = field(default_factory=dict)  # 扩展字段，避免频繁改模型

    def to_dict(self) -> dict[str, Any]:
        """Render the recovery plan as JSON-ready trace data."""

        return {
            "status": self.status,
            "failure_type": self.failure_type,
            "source_type": self.source_type,
            "source_name": self.source_name,
            "reason": self.reason,
            "next_safe_action": self.next_safe_action,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "skill_name": self.skill_name,
            "failed_step": self.failed_step,
            "completed_steps": self.completed_steps,
            "metadata": self.metadata,
        }

    def to_text(self) -> str:
        """Render the recovery plan for CLI, graph output, and human traces."""

        title = "Skill recovery plan" if self.source_type == "skill" else "Tool recovery plan"
        lines = [
            title,
            f"Status: {self.status}",
            f"Failure type: {self.failure_type}",
            f"Source type: {self.source_type}",
            f"Source: {self.source_name}",
        ]
        if self.tool_name:
            lines.append(f"Tool: {self.tool_name}")
        if self.tool_input is not None:
            lines.append(f"Tool input: {self.tool_input}")
        if self.skill_name:
            lines.append(f"Skill: {self.skill_name}")
        if self.failed_step is not None:
            lines.append(f"Failed step: {_format_failed_step(self.failed_step)}")
        if self.completed_steps is not None:
            lines.append(f"Completed steps: {self.completed_steps}")
        lines.extend(
            [
                f"Reason: {self.reason}",
                f"Next safe action: {self.next_safe_action}",
            ]
        )
        return "\n".join(lines)


def build_tool_recovery_plan(tool_name: str, tool_input: dict[str, Any], reason: str) -> RecoveryPlan:
    """Build a standard recovery plan for a failed normal tool call."""

    failure_type = classify_failure(reason)
    return RecoveryPlan(
        status="failed",
        failure_type=failure_type,
        source_type="tool",
        source_name=tool_name,
        reason=reason,
        next_safe_action=_build_tool_next_safe_action(tool_name, tool_input, reason),
        tool_name=tool_name,
        tool_input=tool_input,
    )


def build_skill_recovery_plan(skill_run: dict[str, Any] | None, reason: str = "") -> RecoveryPlan:
    """Build a standard recovery plan for a failed SkillRun trace."""

    if not isinstance(skill_run, dict):
        final_reason = reason or "Skill execution failed without a structured run."
        return RecoveryPlan(
            status="failed",
            failure_type=classify_failure(final_reason),
            source_type="skill",
            source_name="unknown",
            reason=final_reason,
            next_safe_action="Inspect the skill trace and rerun after fixing the missing execution context.",
            skill_name="unknown",
            completed_steps=0,
        )

    failed_step = find_failed_skill_step(skill_run)
    skill_name = extract_skill_name(skill_run)
    final_reason = extract_failure_reason(failed_step, reason or "Skill execution failed.")
    return RecoveryPlan(
        status="failed",
        failure_type=classify_failure(final_reason),
        source_type="skill",
        source_name=skill_name,
        reason=final_reason,
        next_safe_action=_build_skill_next_safe_action(failed_step),
        tool_name=_extract_failed_step_tool_name(failed_step),
        tool_input=_extract_failed_step_tool_input(failed_step),
        skill_name=skill_name,
        failed_step=failed_step,
        completed_steps=_as_int(skill_run.get("completed_steps"), 0),
    )


def build_exception_recovery_plan(reason: str, source_name: str = "unknown") -> RecoveryPlan:
    """Build a standard recovery plan for exceptions before structured run data exists."""

    return RecoveryPlan(
        status="failed",
        failure_type=classify_failure(reason),
        source_type="exception",
        source_name=source_name,
        reason=reason,
        next_safe_action="Inspect the exception, fix the runtime context, and rerun the graph request.",
    )


def classify_failure(reason: str) -> str:
    """Classify common failure messages for deterministic recovery decisions."""

    lowered = reason.lower()
    if "does not exist" in lowered or "not found" in lowered:
        return "missing_resource"
    if "escapes workspace root" in lowered or "permission" in lowered:
        return "unsafe_or_denied_access"
    if "api key" in lowered or "network" in lowered or "connection" in lowered:
        return "external_dependency"
    if "too large" in lowered:
        return "input_too_large"
    return "execution_error"


def find_failed_skill_step(skill_run: dict[str, Any]) -> dict[str, Any] | None:
    """Return the first failed step from a JSON-ready SkillRun trace."""

    steps = skill_run.get("steps", [])
    if not isinstance(steps, list):
        return None
    for step in steps:
        if isinstance(step, dict) and step.get("status") == "failed":
            return step
    return None


def extract_skill_name(skill_run: dict[str, Any]) -> str:
    """Read the selected skill name from a JSON-ready SkillRun trace."""

    skill = skill_run.get("skill", {})
    if isinstance(skill, dict):
        name = skill.get("name")
        if isinstance(name, str):
            return name
    return "unknown"


def extract_failure_reason(failed_step: dict[str, Any] | None, fallback: str) -> str:
    """Find the clearest available reason for a failed skill run."""

    if failed_step:
        error = failed_step.get("error")
        observation = failed_step.get("observation")
        if isinstance(error, str) and error:
            return error
        if isinstance(observation, str) and observation:
            return observation
    return fallback


def _build_tool_next_safe_action(tool_name: str, tool_input: dict[str, Any], reason: str) -> str:
    """Suggest a deterministic next action for a failed normal tool call."""

    failure_type = classify_failure(reason)
    if failure_type == "missing_resource":
        path = tool_input.get("path") or tool_input.get("question") or "the requested input"
        return f"Inspect whether {path} exists in the workspace, correct the input, then rerun {tool_name}."
    if failure_type == "unsafe_or_denied_access":
        return "Use a workspace-relative path that stays inside the project root, then rerun the graph."
    if failure_type == "external_dependency":
        return "Check the required API key or network dependency before rerunning the tool."
    if failure_type == "input_too_large":
        return "Use a smaller file or add a chunked reader before rerunning the tool."
    return f"Inspect the tool input and error message, then rerun {tool_name} with corrected arguments."


def _build_skill_next_safe_action(failed_step: dict[str, Any] | None) -> str:
    """Suggest a deterministic next action for a failed skill step."""

    if not failed_step:
        return "Inspect the skill trace and rerun after fixing the missing execution context."
    tool_name = failed_step.get("tool_name") or "the failed tool"
    tool_input = failed_step.get("tool_input") or "the requested input"
    return f"Inspect {tool_input} for {tool_name}, fix the missing resource or path, then rerun the skill."


def _format_failed_step(failed_step: dict[str, Any]) -> str:
    """Render the failed step without requiring a SkillStepResult instance."""

    return (
        f"{failed_step.get('index')}. {failed_step.get('instruction')} "
        f"(tool={failed_step.get('tool_name')}, input={failed_step.get('tool_input')})"
    )


def _extract_failed_step_tool_name(failed_step: dict[str, Any] | None) -> str | None:
    """Read the tool name from a failed skill step."""

    if failed_step is None:
        return None
    value = failed_step.get("tool_name")
    return value if isinstance(value, str) else None


def _extract_failed_step_tool_input(failed_step: dict[str, Any] | None) -> dict[str, Any] | None:
    """Normalize a failed skill step tool input for the unified recovery model."""

    if failed_step is None:
        return None
    value = failed_step.get("tool_input")
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        return {"value": value}
    return None


def _as_int(value: Any, default: int) -> int:
    """Convert numeric trace values defensively."""

    return value if isinstance(value, int) else default
