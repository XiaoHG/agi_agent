"""Agent-facing adapter for local MCP experiments."""

from __future__ import annotations

from pathlib import Path

from mcp.clients.local_client import LocalMCPClient
from mcp.policy import (
    MCPGovernancePolicy,
    build_default_mcp_governance_policy,
    build_default_mcp_policy,
    evaluate_mcp_tool_permission,
    validate_mcp_request,
)
from mcp.schema import (
    MCPError,
    MCPExecutionRecord,
    MCPPermissionDecision,
    MCPPermissionPolicy,
    MCPRequest,
    MCPRequestValidationResult,
    MCPResponse,
)
from mcp.servers.local_server import LocalMCPServer


def list_mcp_tools(root: Path) -> str:
    """Return available local MCP tools as text."""

    client = _build_client(root)
    lines = ["Available MCP tools:"]
    for spec in client.list_tools():
        lines.append(f"- {spec.name} [{spec.permission_level}]: {spec.description}")
    return "\n".join(lines)


def call_mcp_tool(root: Path, tool_name: str, arguments: dict[str, object] | None = None) -> str:
    """Call a local MCP tool and render the response."""

    response = call_mcp_tool_response(root, tool_name, arguments)
    status = "error" if response.is_error else "ok"
    return f"[mcp:{status}] {response.tool_name}\n{response.content}"


def call_mcp_tool_response(
    root: Path,
    tool_name: str,
    arguments: dict[str, object] | None = None,
    *,
    policy: MCPPermissionPolicy | None = None,
) -> MCPResponse:
    """Call a local MCP tool and preserve structured permission metadata."""

    return call_mcp_tool_exchange(root, tool_name, arguments, policy=policy).to_response()


def call_mcp_tool_exchange(
    root: Path,
    tool_name: str,
    arguments: dict[str, object] | None = None,
    *,
    policy: MCPPermissionPolicy | None = None,
    governance_policy: MCPGovernancePolicy | None = None,
) -> MCPExecutionRecord:
    """Call a local MCP tool and return a standardized execution record."""

    client = _build_client(root)
    spec = client.get_tool_spec(tool_name)
    resolved_policy = policy or build_default_mcp_policy()
    resolved_governance_policy = governance_policy or build_default_mcp_governance_policy()
    request = MCPRequest(tool_name=tool_name, arguments=arguments or {})
    audit_trail: list[dict[str, object]] = []
    if spec is None:
        response = MCPResponse(tool_name, f"Unknown MCP tool: {tool_name}", is_error=True)
        decision = _build_unknown_tool_decision(tool_name)
        error = MCPError(
            stage="lookup",
            code="unknown_tool",
            message=response.content,
            next_safe_action="Choose one of the listed MCP tools and rerun the request.",
        )
        return MCPExecutionRecord(
            request=request,
            response=response,
            permission_policy=resolved_policy,
            permission_decision=decision,
            request_validation=MCPRequestValidationResult(
                tool_name=tool_name,
                valid=False,
                reason=f"Unknown MCP tool: {tool_name}",
            ),
            governance_audit=[{"stage": "lookup", "status": "error", "reason": "unknown tool"}],
            error=error,
            protocol_version=resolved_governance_policy.protocol_version,
        )

    audit_trail.append({"stage": "lookup", "status": "ok", "tool_name": spec.name})
    validation = validate_mcp_request(spec, request, resolved_governance_policy)
    audit_trail.append({"stage": "validation", "status": "ok" if validation.valid else "error", "reason": validation.reason})
    if not validation.valid:
        response = MCPResponse(
            tool_name,
            (
                f"Request validation failed for MCP tool: {tool_name}\n"
                f"Reason: {validation.reason}\n"
                f"Missing arguments: {', '.join(validation.missing_arguments) if validation.missing_arguments else 'none'}\n"
                f"Extra arguments: {', '.join(validation.extra_arguments) if validation.extra_arguments else 'none'}\n"
                f"Next safe action: fix the request shape and rerun the same MCP tool."
            ),
            is_error=True,
            metadata={
                "request_validation": validation.to_dict(),
                "governance_policy": resolved_governance_policy.to_dict(),
            },
        )
        error = MCPError(
            stage="validation",
            code="invalid_request",
            message=response.content,
            next_safe_action="Fix the request shape and rerun the same MCP tool.",
        )
        return MCPExecutionRecord(
            request=request,
            response=response,
            permission_policy=resolved_policy,
            permission_decision=MCPPermissionDecision(
                tool_name=spec.name,
                permission_level=spec.permission_level,
                allowed=False,
                reason=validation.reason,
                next_safe_action="Fix the request shape and rerun the same MCP tool.",
            ),
            request_validation=validation,
            governance_audit=audit_trail,
            error=error,
            protocol_version=resolved_governance_policy.protocol_version,
        )

    decision = evaluate_mcp_tool_permission(spec, resolved_policy)
    audit_trail.append({"stage": "permission", "status": "ok" if decision.allowed else "error", "reason": decision.reason})
    if not decision.allowed:
        response = MCPResponse(
            tool_name,
            (
                f"Permission denied for MCP tool: {tool_name}\n"
                f"Permission level: {decision.permission_level}\n"
                f"Reason: {decision.reason}\n"
                f"Next safe action: {decision.next_safe_action}"
            ),
            is_error=True,
            metadata={
                "permission_decision": decision.to_dict(),
                "permission_policy": resolved_policy.to_dict(),
                "request_validation": validation.to_dict(),
                "governance_policy": resolved_governance_policy.to_dict(),
            },
        )
        error = MCPError(
            stage="permission",
            code=f"permission_denied:{decision.permission_level}",
            message=response.content,
            next_safe_action=decision.next_safe_action,
        )
        return MCPExecutionRecord(
            request=request,
            response=response,
            permission_policy=resolved_policy,
            permission_decision=decision,
            request_validation=validation,
            governance_audit=audit_trail,
            error=error,
            protocol_version=resolved_governance_policy.protocol_version,
        )

    response = client.call_tool(tool_name, validation.normalized_arguments or request.arguments)
    audit_trail.append({"stage": "execution", "status": "error" if response.is_error else "ok", "tool_name": response.tool_name})
    if response.is_error:
        error = MCPError(
            stage="server",
            code="tool_error",
            message=response.content,
            next_safe_action="Inspect the tool input, fix the request, and rerun the same MCP tool.",
        )
    else:
        error = None
    return MCPExecutionRecord(
        request=request,
        response=MCPResponse(
            tool_name=response.tool_name,
            content=response.content,
            is_error=response.is_error,
            metadata={
                "permission_decision": decision.to_dict(),
                "permission_policy": resolved_policy.to_dict(),
                "request_validation": validation.to_dict(),
                "governance_policy": resolved_governance_policy.to_dict(),
                **response.metadata,
            },
        ),
        permission_policy=resolved_policy,
        permission_decision=decision,
        request_validation=validation,
        governance_audit=audit_trail,
        error=error,
        protocol_version=resolved_governance_policy.protocol_version,
    )


def _build_client(root: Path) -> LocalMCPClient:
    """Create the local client/server pair used by the adapter."""

    server = LocalMCPServer(root)
    return LocalMCPClient(server)


def _build_unknown_tool_decision(tool_name: str) -> MCPPermissionDecision:
    """Build a placeholder decision for an unknown tool."""

    return MCPPermissionDecision(
        tool_name=tool_name,
        permission_level="unknown",
        allowed=False,
        reason=f"Unknown MCP tool: {tool_name}",
        next_safe_action="Choose one of the listed MCP tools and rerun the request.",
    )
