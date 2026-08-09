"""Tool-backed skill execution records for the learning workspace."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

from .catalog import SkillSpec, select_skill
from .policy import SkillPolicyDecision, SkillRuntimePolicy, build_default_skill_runtime_policy, evaluate_skill_runtime_policy


@dataclass(frozen=True)
class SkillToolRequest:
    """Tool request emitted by a skill step."""

    tool_name: str  # 需要调用的工具名
    tool_input: str  # 传给工具的输入

    def to_dict(self) -> dict[str, str]:
        """Render the tool request as JSON-ready data."""

        return {
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
        }


@dataclass(frozen=True)
class SkillToolResponse:
    """Tool response returned to the skill runner."""

    tool_name: str  # 实际执行的工具名
    output: str  # 工具输出
    is_error: bool = False  # 工具是否失败

    def to_dict(self) -> dict[str, object]:
        """Render the tool response as JSON-ready data."""

        return {
            "tool_name": self.tool_name,
            "output": self.output,
            "is_error": self.is_error,
        }


@dataclass(frozen=True)
class SkillStep:
    """Executable step definition inside a skill run."""

    index: int  # 步骤序号，从 1 开始
    instruction: str  # 当前步骤说明
    action: str = "record"  # record / tool
    tool_name: str | None = None  # action=tool 时要调用的工具
    tool_input: str | None = None  # action=tool 时传给工具的输入

    def to_dict(self) -> dict[str, object]:
        """Render the executable step spec as JSON-ready data."""

        return {
            "index": self.index,
            "instruction": self.instruction,
            "action": self.action,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
        }


@dataclass(frozen=True)
class SkillStepResult:
    """Execution result for one step inside a skill run."""

    index: int  # 步骤序号，从 1 开始
    instruction: str  # 当前步骤的标准说明
    status: str  # completed / failed
    observation: str  # 当前步骤产生的观察结果
    action: str = "record"  # record / tool
    tool_name: str | None = None  # 本步骤调用的工具
    tool_input: str | None = None  # 本步骤传给工具的输入
    error: str | None = None  # 本步骤失败原因

    def to_text(self) -> str:
        """Render the step result as a trace line."""

        tool_part = ""
        if self.tool_name:
            tool_part = f" tool={self.tool_name} input={self.tool_input or ''}"
        error_part = f" error={self.error}" if self.error else ""
        return (
            f"{self.index}. [{self.status}] {self.instruction}"
            f"{tool_part} -> {self.observation}{error_part}"
        )

    def to_dict(self) -> dict[str, object]:
        """Render the step result as JSON-ready trace data."""

        return {
            "index": self.index,
            "instruction": self.instruction,
            "status": self.status,
            "observation": self.observation,
            "action": self.action,
            "tool_name": self.tool_name,
            "tool_input": self.tool_input,
            "error": self.error,
        }


@dataclass(frozen=True)
class SkillRun:
    """Structured record produced by executing one selected skill."""

    task: str  # 用户原始任务
    skill: SkillSpec  # 被选择并执行的技能
    status: str  # 当前 run 状态
    policy: SkillRuntimePolicy = field(default_factory=build_default_skill_runtime_policy)  # 运行时策略
    policy_decision: SkillPolicyDecision | None = None  # 策略决策
    steps: list[SkillStepResult] = field(default_factory=list)  # 步骤执行结果
    final_output: str = ""  # 面向 Agent 的最终输出

    def to_text(self) -> str:
        """Render the skill run for tools, CLI, and traces."""

        step_lines = [step.to_text() for step in self.steps]
        if not step_lines:
            step_lines = ["- no skill step was executed"]
        return (
            f"Skill run: {self.skill.name}\n"
            f"Skill version: {self.skill.version}\n"
            f"Status: {self.status}\n"
            f"Policy: {self.policy.policy_name}\n"
            f"Policy decision: {self.policy_decision.reason if self.policy_decision else 'n/a'}\n"
            f"Task: {self.task}\n"
            f"Purpose: {self.skill.purpose}\n\n"
            "Executed steps:\n"
            f"{chr(10).join(step_lines)}\n\n"
            f"Final output:\n{self.final_output}"
        )

    def to_dict(self) -> dict[str, object]:
        """Render the skill run as JSON-ready trace data."""

        return {
            "task": self.task,
            "skill": {
                "name": self.skill.name,
                "version": self.skill.version,
                "purpose": self.skill.purpose,
                "output_format": self.skill.output_format,
                "source": self.skill.source,
                "path": self.skill.path,
            },
            "status": self.status,
            "policy": {
                "policy_name": self.policy.policy_name,
                "allow_builtin": self.policy.allow_builtin,
                "allow_project": self.policy.allow_project,
                "allowed_skill_names": list(self.policy.allowed_skill_names),
                "denied_skill_names": list(self.policy.denied_skill_names),
                "minimum_versions": self.policy.minimum_versions,
            },
            "policy_decision": None if self.policy_decision is None else self.policy_decision.to_dict(),
            "step_count": len(self.steps),
            "completed_steps": sum(1 for step in self.steps if step.status == "completed"),
            "failed_steps": sum(1 for step in self.steps if step.status == "failed"),
            "tool_backed_steps": sum(1 for step in self.steps if step.action == "tool"),
            "steps": [step.to_dict() for step in self.steps],
            "final_output": self.final_output,
        }


SkillToolRunner = Callable[[SkillToolRequest], SkillToolResponse]


def execute_skill(
    task: str,
    tool_runner: SkillToolRunner | None = None,
    *,
    root: Path = Path("."),
    skill_name: str | None = None,
    policy: SkillRuntimePolicy | None = None,
) -> SkillRun:
    """Select and execute one built-in or project skill with optional tool-backed steps."""

    resolved_policy = policy or build_default_skill_runtime_policy()
    skill = select_skill(task, root=root, skill_name=skill_name)
    policy_decision = evaluate_skill_runtime_policy(skill, resolved_policy)
    if not policy_decision.allowed:
        return SkillRun(
            task=task,
            skill=skill,
            status="blocked",
            policy=resolved_policy,
            policy_decision=policy_decision,
            steps=[],
            final_output=_build_blocked_output(skill, task, policy_decision),
        )
    step_specs = build_skill_steps(skill, task)
    steps: list[SkillStepResult] = []
    status = "completed"

    for step in step_specs:
        result = _run_step(skill, task, step, tool_runner)
        steps.append(result)
        if result.status == "failed":
            status = "failed"
            break

    return SkillRun(
        task=task,
        skill=skill,
        status=status,
        policy=resolved_policy,
        policy_decision=policy_decision,
        steps=steps,
        final_output=_build_final_output(skill, task, steps, status),
    )


def build_skill_steps(skill: SkillSpec, task: str) -> list[SkillStep]:
    """Build executable step specs for a selected skill."""

    if skill.name == "code_review":
        tool_plan = {
            1: ("list_dir", "."),
            2: ("search_docs", task),
            3: ("search_docs", "project tests evaluation workflow"),
        }
        return _build_steps_with_tools(skill, tool_plan)

    if skill.name == "research_brief":
        tool_plan = {
            2: ("search_docs", task),
            3: ("search_docs", f"sources for {task}"),
        }
        return _build_steps_with_tools(skill, tool_plan)

    if skill.name == "learning_explanation":
        tool_plan = {
            2: ("search_docs", task),
            3: ("read_file", "docs/current-learning-state.md"),
        }
        return _build_steps_with_tools(skill, tool_plan)

    return _build_steps_with_tools(skill, {})


def _build_steps_with_tools(skill: SkillSpec, tool_plan: dict[int, tuple[str, str]]) -> list[SkillStep]:
    """Convert a skill definition into executable step specs."""

    steps: list[SkillStep] = []
    for index, instruction in enumerate(skill.steps, start=1):
        planned_tool = tool_plan.get(index)
        if planned_tool:
            tool_name, tool_input = planned_tool
            steps.append(
                SkillStep(
                    index=index,
                    instruction=instruction,
                    action="tool",
                    tool_name=tool_name,
                    tool_input=tool_input,
                )
            )
        else:
            steps.append(SkillStep(index=index, instruction=instruction))
    return steps


def _run_step(
    skill: SkillSpec,
    task: str,
    step: SkillStep,
    tool_runner: SkillToolRunner | None,
) -> SkillStepResult:
    """Run one skill step and return a structured step result."""

    if step.action == "tool" and step.tool_name:
        if tool_runner is None:
            return SkillStepResult(
                index=step.index,
                instruction=step.instruction,
                status="completed",
                observation=_build_planned_tool_observation(skill, task, step),
                action=step.action,
                tool_name=step.tool_name,
                tool_input=step.tool_input,
            )

        response = tool_runner(SkillToolRequest(step.tool_name, step.tool_input or ""))
        if response.is_error:
            return SkillStepResult(
                index=step.index,
                instruction=step.instruction,
                status="failed",
                observation=response.output,
                action=step.action,
                tool_name=response.tool_name,
                tool_input=step.tool_input,
                error=response.output,
            )
        return SkillStepResult(
            index=step.index,
            instruction=step.instruction,
            status="completed",
            observation=_preview(response.output),
            action=step.action,
            tool_name=response.tool_name,
            tool_input=step.tool_input,
        )

    return SkillStepResult(
        index=step.index,
        instruction=step.instruction,
        status="completed",
        observation=_build_record_observation(skill, task, step.instruction),
        action=step.action,
    )


def _build_record_observation(skill: SkillSpec, task: str, instruction: str) -> str:
    """Create a deterministic observation for a record-only skill step."""

    return f"Prepared {skill.name} step for task '{task}'. Step focus: {instruction}"


def _build_planned_tool_observation(skill: SkillSpec, task: str, step: SkillStep) -> str:
    """Describe the planned tool call when no tool runner is available."""

    return (
        f"Prepared {skill.name} tool step for task '{task}'. "
        f"Planned tool: {step.tool_name}; input: {step.tool_input or ''}"
    )


def _build_final_output(
    skill: SkillSpec,
    task: str,
    steps: list[SkillStepResult],
    status: str,
) -> str:
    """Build the final output for a completed or failed skill run."""

    completed = sum(1 for step in steps if step.status == "completed")
    failed = sum(1 for step in steps if step.status == "failed")
    tool_steps = sum(1 for step in steps if step.action == "tool")

    return (
        f"Executed skill '{skill.name}' for task '{task}' with status '{status}'. "
        f"Completed steps: {completed}; failed steps: {failed}; tool-backed steps: {tool_steps}. "
        f"Expected output format: {skill.output_format}"
    )


def _build_blocked_output(skill: SkillSpec, task: str, decision: SkillPolicyDecision) -> str:
    """Build the final output for a policy-blocked skill run."""

    return (
        f"Blocked skill '{skill.name}' for task '{task}' under policy '{decision.policy_name}'. "
        f"Reason: {decision.reason} "
        f"Next safe action: {decision.next_safe_action}"
    )


def _preview(text: str, limit: int = 240) -> str:
    """Keep tool output compact inside skill step observations."""

    normalized = " ".join(text.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 15] + "... (truncated)"
