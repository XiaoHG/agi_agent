"""Deterministic skill execution records for the learning workspace."""

from __future__ import annotations

from dataclasses import dataclass, field

from .catalog import SkillSpec, select_skill


@dataclass(frozen=True)
class SkillStepResult:
    """Execution result for one step inside a skill run."""

    index: int  # 步骤序号，从 1 开始
    instruction: str  # 当前步骤的标准说明
    status: str  # 当前阶段只使用 completed，后续可扩展 failed/skipped
    observation: str  # 当前步骤产生的确定性观察结果

    def to_text(self) -> str:
        """Render the step result as a trace line."""

        return f"{self.index}. [{self.status}] {self.instruction} -> {self.observation}"


@dataclass(frozen=True)
class SkillRun:
    """Structured record produced by executing one selected skill."""

    task: str  # 用户原始任务
    skill: SkillSpec  # 被选择并执行的技能
    status: str  # 当前 run 状态
    steps: list[SkillStepResult] = field(default_factory=list)  # 步骤执行结果
    final_output: str = ""  # 面向 Agent 的最终输出

    def to_text(self) -> str:
        """Render the skill run for tools, CLI, and traces."""

        step_lines = [step.to_text() for step in self.steps]
        if not step_lines:
            step_lines = ["- no skill step was executed"]
        return (
            f"Skill run: {self.skill.name}\n"
            f"Status: {self.status}\n"
            f"Task: {self.task}\n"
            f"Purpose: {self.skill.purpose}\n\n"
            "Executed steps:\n"
            f"{chr(10).join(step_lines)}\n\n"
            f"Final output:\n{self.final_output}"
        )


def execute_skill(task: str) -> SkillRun:
    """Select and execute one built-in skill with deterministic step records."""

    skill = select_skill(task)
    steps = [
        SkillStepResult(
            index=index,
            instruction=instruction,
            status="completed",
            observation=_build_step_observation(skill, task, instruction),
        )
        for index, instruction in enumerate(skill.steps, start=1)
    ]
    return SkillRun(
        task=task,
        skill=skill,
        status="completed",
        steps=steps,
        final_output=_build_final_output(skill, task),
    )


def _build_step_observation(skill: SkillSpec, task: str, instruction: str) -> str:
    """Create a deterministic observation for one skill step."""

    return (
        f"Prepared {skill.name} step for task '{task}'. "
        f"Step focus: {instruction}"
    )


def _build_final_output(skill: SkillSpec, task: str) -> str:
    """Build the deterministic final output for a completed skill run."""

    return (
        f"Executed skill '{skill.name}' for task '{task}'. "
        f"Expected output format: {skill.output_format}"
    )
