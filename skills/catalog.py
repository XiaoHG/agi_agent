"""Small skill catalog used by the current Agent stage."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SkillSpec:
    """Reusable task capability that can be selected by the Agent."""

    name: str  # 技能名，用于选择和展示
    purpose: str  # 技能解决的问题
    steps: tuple[str, ...]  # 标准执行步骤
    output_format: str  # 期望输出格式

    def describe(self) -> str:
        """Render one skill as a compact text block."""

        lines = [
            f"Skill: {self.name}",
            f"Purpose: {self.purpose}",
            "Steps:",
        ]
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. {step}")
        lines.append(f"Output format: {self.output_format}")
        return "\n".join(lines)


def get_builtin_skills() -> list[SkillSpec]:
    """Return built-in skills for the learning project."""

    return [
        SkillSpec(
            name="research_brief",
            purpose="Collect local context and produce a short research brief.",
            steps=(
                "Clarify the research question.",
                "Search local project documents.",
                "Extract key findings with sources.",
                "Summarize limits and next actions.",
            ),
            output_format="Brief with findings, sources, limits, and next actions.",
        ),
        SkillSpec(
            name="code_review",
            purpose="Review code changes for correctness, tests, and maintainability.",
            steps=(
                "Inspect changed files.",
                "Check behavior and edge cases.",
                "Run relevant tests.",
                "Report issues and safe fixes.",
            ),
            output_format="Review notes with issues, evidence, and recommended fixes.",
        ),
        SkillSpec(
            name="learning_explanation",
            purpose="Explain project code or concepts for learning.",
            steps=(
                "Identify the learner question.",
                "Map the concept to project files.",
                "Explain the execution flow.",
                "List common mistakes and exercises.",
            ),
            output_format="Explanation with flow, key points, mistakes, and practice tasks.",
        ),
    ]


def describe_skills() -> str:
    """Render all built-in skills."""

    parts = ["Available skills:"]
    for skill in get_builtin_skills():
        parts.append(skill.describe())
    return "\n\n".join(parts)


def select_skill(user_input: str) -> SkillSpec:
    """Select one built-in skill using simple deterministic rules."""

    lowered = user_input.lower()
    if "review" in lowered or "bug" in lowered or "test" in lowered:
        return _get_skill("code_review")
    if "explain" in lowered or "learn" in lowered or "understand" in lowered:
        return _get_skill("learning_explanation")
    return _get_skill("research_brief")


def _get_skill(name: str) -> SkillSpec:
    """Return a built-in skill by name."""

    for skill in get_builtin_skills():
        if skill.name == name:
            return skill
    raise ValueError(f"Unknown skill: {name}")
