"""Permission policy helpers for the local MCP learning layer."""

from __future__ import annotations

from dataclasses import dataclass
import os

from .schema import (
    DESTRUCTIVE_PERMISSION,
    MCPPermissionDecision,
    MCPPermissionPolicy,
    MCPRequest,
    MCPRequestValidationResult,
    MCPToolSpec,
    NETWORK_PERMISSION,
    READ_ONLY_PERMISSION,
    WRITE_PERMISSION,
)


@dataclass(frozen=True)
class MCPGovernancePolicy:
    """Policy that controls MCP request validation and audit behavior."""

    protocol_version: str = "v2"                    # 治理协议版本
    reject_unknown_arguments: bool = True           # 是否拒绝多余参数
    reject_missing_required_arguments: bool = True  # 是否拒绝缺失必填参数

    def to_dict(self) -> dict[str, object]:
        """Render the governance policy as JSON-ready data."""

        return {
            "protocol_version": self.protocol_version,
            "reject_unknown_arguments": self.reject_unknown_arguments,
            "reject_missing_required_arguments": self.reject_missing_required_arguments,
        }


def build_default_mcp_policy() -> MCPPermissionPolicy:
    """Return the default project policy for MCP tool execution."""

    return MCPPermissionPolicy(
        allow_read_only=True,
        allow_write=False,
        allow_network=False,
        allow_destructive=False,
    )


def build_default_mcp_governance_policy() -> MCPGovernancePolicy:
    """Return the default governance policy for MCP request validation."""

    return MCPGovernancePolicy()


def build_environment_mcp_policy(env: dict[str, str] | None = None) -> MCPPermissionPolicy:
    """Return a permission policy derived from environment variables."""

    resolved_env = env or os.environ
    profile = resolved_env.get("AGI_AGENT_MCP_POLICY_PROFILE", "default").strip() or "default"
    if profile == "read-only":
        return MCPPermissionPolicy(
            allow_read_only=True,
            allow_write=False,
            allow_network=False,
            allow_destructive=False,
        )
    if profile == "write-enabled":
        return MCPPermissionPolicy(
            allow_read_only=True,
            allow_write=True,
            allow_network=False,
            allow_destructive=False,
        )
    if profile == "open":
        return MCPPermissionPolicy(
            allow_read_only=True,
            allow_write=True,
            allow_network=True,
            allow_destructive=False,
        )
    return build_default_mcp_policy()


def build_environment_mcp_governance_policy(env: dict[str, str] | None = None) -> MCPGovernancePolicy:
    """Return a governance policy derived from environment variables."""

    resolved_env = env or os.environ
    profile = resolved_env.get("AGI_AGENT_MCP_GOVERNANCE_PROFILE", "v2").strip() or "v2"
    return MCPGovernancePolicy(protocol_version=profile)


def evaluate_mcp_tool_permission(spec: MCPToolSpec, policy: MCPPermissionPolicy) -> MCPPermissionDecision:
    """Evaluate whether one MCP tool may run under the given policy."""

    allowed = policy.allows(spec.permission_level)
    if allowed:
        return MCPPermissionDecision(
            tool_name=spec.name,
            permission_level=spec.permission_level,
            allowed=True,
            reason=f"Policy allows MCP tools with permission level '{spec.permission_level}'.",
            next_safe_action=f"Proceed to call {spec.name} through the MCP adapter.",
        )

    return MCPPermissionDecision(
        tool_name=spec.name,
        permission_level=spec.permission_level,
        allowed=False,
        reason=_build_denial_reason(spec.permission_level),
        next_safe_action=_build_next_safe_action(spec.permission_level),
    )


def validate_mcp_request(
    spec: MCPToolSpec,
    request: MCPRequest,
    policy: MCPGovernancePolicy,
) -> MCPRequestValidationResult:
    """Validate and normalize one MCP request against the tool schema."""

    arguments = request.arguments if isinstance(request.arguments, dict) else {}
    schema = spec.input_schema if isinstance(spec.input_schema, dict) else {}
    properties = schema.get("properties", {}) if isinstance(schema.get("properties", {}), dict) else {}
    required = schema.get("required", []) if isinstance(schema.get("required", []), list) else []

    missing = tuple(name for name in required if name not in arguments or _is_blank_argument(arguments.get(name)))
    extra = tuple(name for name in arguments if name not in properties)
    normalized = {
        name: value
        for name, value in arguments.items()
        if name in properties
    } if properties else dict(arguments)

    if missing and policy.reject_missing_required_arguments:
        return MCPRequestValidationResult(
            tool_name=spec.name,
            valid=False,
            reason=f"Missing required argument(s): {', '.join(missing)}",
            missing_arguments=missing,
            extra_arguments=extra,
            normalized_arguments=normalized,
        )
    if extra and policy.reject_unknown_arguments:
        return MCPRequestValidationResult(
            tool_name=spec.name,
            valid=False,
            reason=f"Unexpected argument(s): {', '.join(extra)}",
            missing_arguments=missing,
            extra_arguments=extra,
            normalized_arguments=normalized,
        )

    return MCPRequestValidationResult(
        tool_name=spec.name,
        valid=True,
        reason="Request matched the tool schema.",
        missing_arguments=missing,
        extra_arguments=extra,
        normalized_arguments=normalized,
    )


def _build_denial_reason(permission_level: str) -> str:
    """Explain why the current policy denied this tool class."""

    if permission_level == WRITE_PERMISSION:
        return "Write-capable MCP tools are denied by the current read-only policy."
    if permission_level == NETWORK_PERMISSION:
        return "Network-capable MCP tools are denied by the current offline-first policy."
    if permission_level == DESTRUCTIVE_PERMISSION:
        return "Destructive MCP tools are denied by the current safety policy."
    if permission_level == READ_ONLY_PERMISSION:
        return "Read-only MCP tools are denied by the current policy."
    return f"Unknown MCP permission level: {permission_level}"


def _build_next_safe_action(permission_level: str) -> str:
    """Suggest the next safe action after a permission denial."""

    if permission_level == WRITE_PERMISSION:
        return "Choose a read-only MCP tool, or rerun with a policy that explicitly allows write tools."
    if permission_level == NETWORK_PERMISSION:
        return "Use a local read-only MCP tool, or rerun with a policy that explicitly allows network tools."
    if permission_level == DESTRUCTIVE_PERMISSION:
        return "Do not retry automatically. Require explicit approval and a stricter review before allowing this tool."
    return "Inspect the MCP tool policy and rerun with an explicit allow rule only if the action is necessary."


def _is_blank_argument(value: object) -> bool:
    """Return whether an argument should count as missing."""

    return value is None or (isinstance(value, str) and not value.strip())
