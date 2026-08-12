"""Skill catalog and project skill registry for the learning workspace."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re

from .policy import (
    SkillGovernancePolicy,
    SkillRuntimePolicy,
    build_default_skill_governance_policy,
    evaluate_skill_runtime_policy,
    validate_skill_governance,
)


PROJECT_SKILLS_DIR = Path(".codex/skills")
FRONTMATTER_BOUNDARY = "---"
FRONTMATTER_PATTERN = re.compile(r"^(?P<key>[A-Za-z0-9_-]+):\s*(?P<value>.+?)\s*$")
NUMBERED_STEP_PATTERN = re.compile(r"^\d+\.\s+(?P<step>.+?)\s*$")
CODE_FENCE_PATTERN = re.compile(r"```(?:text)?\n(?P<body>.*?)```", re.DOTALL)


@dataclass(frozen=True)
class SkillSpec:
    """Reusable task capability that can be selected by the Agent."""

    name: str                               # 技能名，用于选择和展示
    purpose: str                            # 技能解决的问题
    steps: tuple[str, ...]                  # 标准执行步骤
    output_format: str                      # 期望输出格式
    version: str = "v1"                     # 技能版本
    source: str = "builtin"                 # builtin / project
    path: str | None = None                 # project skill 对应的文件路径
    aliases: tuple[str, ...] = ()           # 可用于显式匹配的别名
    declared_tools: tuple[str, ...] = ()    # skill 显式声明可使用的工具

    def describe(self) -> str:
        """Render one skill as a compact text block."""

        lines = [
            f"Skill: {self.name}",
            f"Version: {self.version}",
            f"Purpose: {self.purpose}",
            f"Source: {self.source}",
        ]
        if self.path:
            lines.append(f"Path: {self.path}")
        lines.append(
            "Declared tools: "
            + (", ".join(self.declared_tools) if self.declared_tools else "<none>")
        )
        lines.extend([
            "Steps:",
        ])
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
            version="v1",
            declared_tools=("search_docs",),
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
            version="v1",
            declared_tools=("list_dir", "search_docs"),
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
            version="v1",
            declared_tools=("search_docs", "read_file"),
        ),
    ]


def discover_project_skills(root: Path = Path(".")) -> list[SkillSpec]:
    """Load project skills from .codex/skills/*/SKILL.md."""

    skill_specs: list[SkillSpec] = []
    skills_dir = (root / PROJECT_SKILLS_DIR).resolve()
    if not skills_dir.exists():
        return skill_specs

    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        spec = _parse_project_skill(root.resolve(), skill_file)
        if spec is not None:
            skill_specs.append(spec)
    return skill_specs


def get_available_skills(root: Path = Path(".")) -> list[SkillSpec]:
    """Return built-in and project skills as one merged catalog."""

    merged: dict[str, SkillSpec] = {}
    for skill in get_builtin_skills():
        merged[_normalize_skill_token(skill.name)] = skill
    for skill in discover_project_skills(root):
        merged[_normalize_skill_token(skill.name)] = skill
    return list(merged.values())


def describe_skills(
    root: Path = Path("."),
    policy: SkillRuntimePolicy | None = None,
    governance_policy: SkillGovernancePolicy | None = None,
) -> str:
    """Render the merged skill catalog."""

    parts = ["Available skills:"]
    if policy is not None:
        parts.append(policy.describe())
    resolved_governance_policy = governance_policy or build_default_skill_governance_policy()
    parts.append(f"Governance protocol: {resolved_governance_policy.protocol_version}")
    for skill in get_available_skills(root):
        executable_tools = _infer_executable_tools(skill)
        validation = validate_skill_governance(
            skill,
            executable_tools=executable_tools,
            policy=resolved_governance_policy,
        )
        decision = evaluate_skill_runtime_policy(skill, policy)
        parts.append(skill.describe())
        parts.append(f"Governance validation: {'valid' if validation.valid else 'blocked'}")
        parts.append(f"Governance reason: {validation.reason}")
        parts.append(f"Policy decision: {'allowed' if decision.allowed else 'blocked'}")
        parts.append(f"Policy reason: {decision.reason}")
    return "\n\n".join(parts)


def select_skill(user_input: str, root: Path = Path("."), skill_name: str | None = None) -> SkillSpec:
    """Select one built-in or project skill using deterministic rules."""

    skills = get_available_skills(root)
    explicit_name = skill_name or _extract_explicit_skill_name(user_input)
    if explicit_name:
        return _get_skill(explicit_name, skills)

    lowered = user_input.lower()
    if "professional code review" in lowered or "release readiness" in lowered:
        matched = _find_skill_by_token(skills, "professional-code-review")
        if matched is not None:
            return matched
    if "review" in lowered or "bug" in lowered or "test" in lowered:
        return _get_skill("code_review", skills)
    if "explain" in lowered or "learn" in lowered or "understand" in lowered:
        return _get_skill("learning_explanation", skills)
    return _get_skill("research_brief", skills)


def _get_skill(name: str, skills: list[SkillSpec] | None = None) -> SkillSpec:
    """Return a skill by name or alias."""

    available_skills = skills or get_available_skills()
    matched = _find_skill_by_token(available_skills, name)
    if matched is not None:
        return matched
    raise ValueError(f"Unknown skill: {name}")


def _find_skill_by_token(skills: list[SkillSpec], raw_token: str) -> SkillSpec | None:
    """Find a skill by normalized name or alias token."""

    target = _normalize_skill_token(raw_token)
    for skill in skills:
        skill_tokens = {_normalize_skill_token(skill.name), *(_normalize_skill_token(alias) for alias in skill.aliases)}
        if target in skill_tokens:
            return skill
    return None


def _extract_explicit_skill_name(user_input: str) -> str | None:
    """Extract an explicit skill selector from the user task."""

    match = re.search(r"skill\s*[:=]\s*(?P<name>[A-Za-z0-9_.-]+)", user_input, re.IGNORECASE)
    if match:
        return match.group("name")

    lowered = user_input.lower()
    markers = [
        "execute skill for ",
        "execute skill ",
        "run skill for ",
        "run skill ",
        "plan skill for ",
        "plan skill ",
        "use skill for ",
        "use skill ",
    ]
    for marker in markers:
        if marker in lowered:
            candidate = user_input[lowered.index(marker) + len(marker) :].strip(" .:")
            if candidate and len(candidate.split()) <= 4:
                return candidate
    return None


def _parse_project_skill(workspace_root: Path, skill_file: Path) -> SkillSpec | None:
    """Parse one project skill markdown file into a SkillSpec."""

    text = skill_file.read_text(encoding="utf-8")
    frontmatter, body = _split_frontmatter(text)
    metadata = _parse_frontmatter(frontmatter)
    name = metadata.get("name", skill_file.parent.name)
    version = metadata.get("version", "v1")
    purpose = metadata.get("description", f"Project skill loaded from {skill_file.parent.name}.")
    steps = _parse_skill_steps(body)
    if not steps:
        steps = ("Inspect the skill instructions.", "Execute the documented workflow.", "Report the result clearly.")
    output_format = _parse_output_format(body)
    relative_path = str(skill_file.resolve().relative_to(workspace_root))
    aliases = tuple(dict.fromkeys({_slug_to_identifier(name), skill_file.parent.name, name.replace("-", " ")}))
    declared_tools = _parse_csv_tuple(metadata.get("tools", ""))
    return SkillSpec(
        name=name,
        purpose=purpose,
        steps=steps,
        output_format=output_format,
        version=version,
        source="project",
        path=relative_path,
        aliases=aliases,
        declared_tools=declared_tools,
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    """Split markdown frontmatter from body content."""

    if not text.startswith(f"{FRONTMATTER_BOUNDARY}\n"):
        return "", text
    parts = text.split(f"\n{FRONTMATTER_BOUNDARY}\n", 1)
    if len(parts) != 2:
        return "", text
    return parts[0].removeprefix(f"{FRONTMATTER_BOUNDARY}\n"), parts[1]


def _parse_frontmatter(text: str) -> dict[str, str]:
    """Parse simple YAML-like frontmatter key-value pairs."""

    metadata: dict[str, str] = {}
    for line in text.splitlines():
        match = FRONTMATTER_PATTERN.match(line.strip())
        if match:
            metadata[match.group("key").lower()] = match.group("value").strip()
    return metadata


def _parse_skill_steps(body: str) -> tuple[str, ...]:
    """Extract top-level numbered workflow steps from markdown."""

    steps: list[str] = []
    for line in body.splitlines():
        match = NUMBERED_STEP_PATTERN.match(line.strip())
        if match:
            steps.append(match.group("step"))
    return tuple(steps)


def _parse_output_format(body: str) -> str:
    """Extract output format guidance from markdown, or use a stable fallback."""

    heading = "## Output format"
    if heading in body:
        section = body.split(heading, 1)[1]
        block_match = CODE_FENCE_PATTERN.search(section)
        if block_match:
            return " ".join(block_match.group("body").split())
    return "Structured skill result with purpose, executed steps, and final output."


def _normalize_skill_token(value: str) -> str:
    """Normalize a skill token for matching."""

    return re.sub(r"[^a-z0-9]+", "", value.lower())


def _slug_to_identifier(name: str) -> str:
    """Convert a slug-like skill name into an underscore identifier."""

    return name.replace("-", "_")


def _parse_csv_tuple(value: str) -> tuple[str, ...]:
    """Parse one comma-separated metadata value into a stable tuple."""

    if not value.strip():
        return ()
    return tuple(item.strip() for item in value.split(",") if item.strip())


def _infer_executable_tools(skill: SkillSpec) -> tuple[str, ...]:
    """Infer the deterministic tool set for registry governance views."""

    if skill.name == "code_review":
        return ("list_dir", "search_docs")
    if skill.name == "research_brief":
        return ("search_docs",)
    if skill.name == "learning_explanation":
        return ("search_docs", "read_file")
    return ()
