"""Permission policy helpers for the local MCP learning layer."""

from __future__ import annotations

from .schema import (
    DESTRUCTIVE_PERMISSION,
    MCPPermissionDecision,
    MCPPermissionPolicy,
    MCPToolSpec,
    NETWORK_PERMISSION,
    READ_ONLY_PERMISSION,
    WRITE_PERMISSION,
)


def build_default_mcp_policy() -> MCPPermissionPolicy:
    """Return the default project policy for MCP tool execution."""

    return MCPPermissionPolicy(
        allow_read_only=True,
        allow_write=False,
        allow_network=False,
        allow_destructive=False,
    )


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
