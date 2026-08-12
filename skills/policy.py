"""Runtime policy for skill governance."""

from __future__ import annotations

from dataclasses import dataclass, field
import re
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .catalog import SkillSpec

#like："1.5.2" to (1,5,2)
def _version_key(value: str) -> tuple[int, ...]:
    """Convert a version label into a sortable numeric key."""

    parts = [int(part) for part in re.findall(r"\d+", value)]
    return tuple(parts) if parts else (0,)


@dataclass(frozen=True)
class SkillRuntimePolicy:
    """Policy that governs which skills may run in the current runtime."""

    policy_name: str = "default"                # 策略名称
    allow_builtin: bool = True                  # 是否允许 builtin skill
    allow_project: bool = True                  # 是否允许 project skill
    allowed_skill_names: tuple[str, ...] = ()   # 白名单技能名
    denied_skill_names: tuple[str, ...] = ()    # 黑名单技能名
    minimum_versions: dict[str, str] = field(default_factory=dict)  # 各技能最低版本要求

    def describe(self) -> str:
        """Render the policy as a compact text block."""

        allowed = ", ".join(self.allowed_skill_names) if self.allowed_skill_names else "<any>"
        denied = ", ".join(self.denied_skill_names) if self.denied_skill_names else "<none>"
        minimum_versions = ", ".join(f"{name}>={version}" for name, version in sorted(self.minimum_versions.items()))
        if not minimum_versions:
            minimum_versions = "<none>"
        return (
            f"Policy: {self.policy_name}\n"
            f"Allow builtin: {self.allow_builtin}\n"
            f"Allow project: {self.allow_project}\n"
            f"Allowed skills: {allowed}\n"
            f"Denied skills: {denied}\n"
            f"Minimum versions: {minimum_versions}"
        )


@dataclass(frozen=True)
class SkillPolicyDecision:
    """Decision made by the runtime policy for one skill."""

    policy_name: str        # 决策来源策略名
    skill_name: str         # 被评估的技能名
    skill_version: str      # 被评估的技能版本
    allowed: bool           # 是否允许执行
    reason: str             # 允许或拒绝原因
    next_safe_action: str   # 下一步安全动作

    def to_dict(self) -> dict[str, str | bool]:
        """Render the decision as JSON-ready data."""

        return {
            "policy_name": self.policy_name,
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "allowed": self.allowed,
            "reason": self.reason,
            "next_safe_action": self.next_safe_action,
        }


@dataclass(frozen=True)
class SkillGovernancePolicy:
    """Policy that validates skill registry entries before execution."""

    protocol_version: str = "v2"                        # 技能治理协议版本
    require_versioned_skills: bool = True               # 是否要求 skill 显式带版本
    require_purpose: bool = True                        # 是否要求 skill 有用途说明
    require_output_format: bool = True                  # 是否要求 skill 有输出格式
    require_declared_tools_for_tool_steps: bool = True  # tool step 是否必须被声明

    def to_dict(self) -> dict[str, object]:
        """Render the governance policy as JSON-ready data."""

        return {
            "protocol_version": self.protocol_version,
            "require_versioned_skills": self.require_versioned_skills,
            "require_purpose": self.require_purpose,
            "require_output_format": self.require_output_format,
            "require_declared_tools_for_tool_steps": self.require_declared_tools_for_tool_steps,
        }


@dataclass(frozen=True)
class SkillGovernanceValidation:
    """Structured validation result for one skill registry entry."""

    skill_name: str         # 技能名
    skill_version: str      # 技能版本
    valid: bool             # 是否通过治理校验
    reason: str             # 总体校验结论
    missing_fields: tuple[str, ...] = ()    # 缺失字段
    undeclared_tools: tuple[str, ...] = ()  # 未声明却会执行的工具
    executable_tools: tuple[str, ...] = ()  # 本次 run 可执行工具
    declared_tools: tuple[str, ...] = ()    # skill 自声明工具

    def to_dict(self) -> dict[str, object]:
        """Render the validation result as JSON-ready data."""

        return {
            "skill_name": self.skill_name,
            "skill_version": self.skill_version,
            "valid": self.valid,
            "reason": self.reason,
            "missing_fields": list(self.missing_fields),
            "undeclared_tools": list(self.undeclared_tools),
            "executable_tools": list(self.executable_tools),
            "declared_tools": list(self.declared_tools),
        }


def build_default_skill_runtime_policy() -> SkillRuntimePolicy:
    """Return the permissive default runtime policy used by the learning project."""

    return SkillRuntimePolicy()


def build_default_skill_governance_policy() -> SkillGovernancePolicy:
    """Return the default governance policy for skill registry validation."""

    return SkillGovernancePolicy()


def evaluate_skill_runtime_policy(skill: SkillSpec, policy: SkillRuntimePolicy | None = None) -> SkillPolicyDecision:
    """Evaluate whether a skill may run under the given policy."""

    resolved_policy = policy or build_default_skill_runtime_policy()
    if skill.name in resolved_policy.denied_skill_names:
        return SkillPolicyDecision(
            policy_name=resolved_policy.policy_name,
            skill_name=skill.name,
            skill_version=skill.version,
            allowed=False,
            reason=f"Skill '{skill.name}' is explicitly denied by runtime policy.",
            next_safe_action="Choose a different skill or relax the deny list.",
        )
    if resolved_policy.allowed_skill_names and skill.name not in resolved_policy.allowed_skill_names:
        return SkillPolicyDecision(
            policy_name=resolved_policy.policy_name,
            skill_name=skill.name,
            skill_version=skill.version,
            allowed=False,
            reason=f"Skill '{skill.name}' is not in the policy allow list.",
            next_safe_action="Add the skill to the allow list or choose an allowed skill.",
        )
    if skill.source == "builtin" and not resolved_policy.allow_builtin:
        return SkillPolicyDecision(
            policy_name=resolved_policy.policy_name,
            skill_name=skill.name,
            skill_version=skill.version,
            allowed=False,
            reason=f"Builtin skill '{skill.name}' is disabled by runtime policy.",
            next_safe_action="Enable builtin skills or choose a project skill.",
        )
    if skill.source == "project" and not resolved_policy.allow_project:
        return SkillPolicyDecision(
            policy_name=resolved_policy.policy_name,
            skill_name=skill.name,
            skill_version=skill.version,
            allowed=False,
            reason=f"Project skill '{skill.name}' is disabled by runtime policy.",
            next_safe_action="Enable project skills or choose a builtin skill.",
        )
    minimum_version = resolved_policy.minimum_versions.get(skill.name)
    if minimum_version and _version_key(skill.version) < _version_key(minimum_version):
        return SkillPolicyDecision(
            policy_name=resolved_policy.policy_name,
            skill_name=skill.name,
            skill_version=skill.version,
            allowed=False,
            reason=f"Skill '{skill.name}' version {skill.version} is below the minimum required {minimum_version}.",
            next_safe_action="Upgrade the skill version or relax the minimum version requirement.",
        )
    return SkillPolicyDecision(
        policy_name=resolved_policy.policy_name,
        skill_name=skill.name,
        skill_version=skill.version,
        allowed=True,
        reason=f"Policy allows skill '{skill.name}' version {skill.version}.",
        next_safe_action=f"Proceed with {skill.name}.",
    )


def validate_skill_governance(
    skill: SkillSpec,
    *,
    executable_tools: tuple[str, ...] = (),
    policy: SkillGovernancePolicy | None = None,
) -> SkillGovernanceValidation:
    """Validate one skill registry entry against governance rules."""

    resolved_policy = policy or build_default_skill_governance_policy()
    missing_fields: list[str] = []
    if resolved_policy.require_versioned_skills and not skill.version.strip():
        missing_fields.append("version")
    if resolved_policy.require_purpose and not skill.purpose.strip():
        missing_fields.append("purpose")
    if resolved_policy.require_output_format and not skill.output_format.strip():
        missing_fields.append("output_format")
    if not skill.steps:
        missing_fields.append("steps")

    undeclared_tools: tuple[str, ...] = ()
    if resolved_policy.require_declared_tools_for_tool_steps and executable_tools:
        declared = {_normalize_governance_token(name) for name in skill.declared_tools}
        undeclared_tools = tuple(
            tool for tool in executable_tools if _normalize_governance_token(tool) not in declared
        )

    if missing_fields:
        return SkillGovernanceValidation(
            skill_name=skill.name,
            skill_version=skill.version,
            valid=False,
            reason=f"Skill registry entry is missing required field(s): {', '.join(missing_fields)}",
            missing_fields=tuple(missing_fields),
            undeclared_tools=undeclared_tools,
            executable_tools=executable_tools,
            declared_tools=skill.declared_tools,
        )
    if undeclared_tools:
        return SkillGovernanceValidation(
            skill_name=skill.name,
            skill_version=skill.version,
            valid=False,
            reason=f"Skill uses undeclared tool(s): {', '.join(undeclared_tools)}",
            undeclared_tools=undeclared_tools,
            executable_tools=executable_tools,
            declared_tools=skill.declared_tools,
        )
    return SkillGovernanceValidation(
        skill_name=skill.name,
        skill_version=skill.version,
        valid=True,
        reason="Skill registry entry passed governance validation.",
        executable_tools=executable_tools,
        declared_tools=skill.declared_tools,
    )


def _normalize_governance_token(value: str) -> str:
    """Normalize skill governance tokens for comparison."""

    return value.strip().lower().replace("-", "_")
