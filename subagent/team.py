"""Deterministic subagent planning for learning multi-agent boundaries."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SubagentSpec:
    """Role definition for one project subagent."""

    name: str  # 角色名
    responsibility: str  # 核心职责
    handoff_rule: str  # 什么时候交给这个角色


@dataclass(frozen=True)
class CollaborationPlan:
    """A small ordered plan that assigns work to subagents."""

    objective: str  # 用户目标
    assigned_roles: tuple[SubagentSpec, ...]  # 参与角色
    steps: tuple[str, ...]  # 协作步骤

    def to_text(self) -> str:
        """Render the collaboration plan."""

        lines = [f"Collaboration objective: {self.objective}", "Assigned roles:"]
        for role in self.assigned_roles:
            lines.append(f"- {role.name}: {role.responsibility}")
        lines.append("Workflow:")
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. {step}")
        return "\n".join(lines)


def get_default_subagents() -> tuple[SubagentSpec, ...]:
    """Return the default project subagents."""

    return (
        SubagentSpec(
            name="teacher_agent",
            responsibility="Explain concepts, architecture, code flow, and learning checkpoints.",
            handoff_rule="Use for learning, explanation, review, and planning questions.",
        ),
        SubagentSpec(
            name="coding_agent",
            responsibility="Implement changes, fix bugs, add tests, and verify behavior.",
            handoff_rule="Use for code changes, debugging, tests, and validation.",
        ),
    )


def describe_subagents() -> str:
    """Render available subagents."""

    lines = ["Available subagents:"]
    for role in get_default_subagents():
        lines.append(f"- {role.name}: {role.responsibility}")
        lines.append(f"  Handoff: {role.handoff_rule}")
    return "\n".join(lines)


def build_collaboration_plan(user_input: str) -> CollaborationPlan:
    """Build a simple collaboration plan for a user request."""

    roles = get_default_subagents()
    lowered = user_input.lower()

    if any(keyword in lowered for keyword in ("implement", "fix", "test", "code", "bug")):
        steps = (
            "Teacher Agent explains the target behavior and design boundary.",
            "Coding Agent implements the smallest safe change.",
            "Coding Agent runs relevant tests.",
            "Teacher Agent summarizes what should be learned from the change.",
        )
        return CollaborationPlan(user_input, roles, steps)

    steps = (
        "Teacher Agent explains the concept and maps it to project files.",
        "Teacher Agent defines a learning checkpoint.",
        "Coding Agent is only involved if the explanation reveals a required code change.",
    )
    return CollaborationPlan(user_input, (roles[0],), steps)
