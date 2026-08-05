"""Small protocol models for local MCP experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


READ_ONLY_PERMISSION = "read_only"
WRITE_PERMISSION = "write"
NETWORK_PERMISSION = "network"
DESTRUCTIVE_PERMISSION = "destructive"


@dataclass(frozen=True)
class MCPToolSpec:
    """Description of one tool exposed by an MCP server."""

    name: str  # 工具名，client 通过它选择要调用的能力
    description: str  # 工具用途说明
    input_schema: dict[str, Any] = field(default_factory=dict)  # 简化版输入 schema
    permission_level: str = READ_ONLY_PERMISSION  # read_only / write / network / destructive


@dataclass(frozen=True)
class MCPRequest:
    """Request sent from a client to an MCP server."""

    tool_name: str  # 要调用的工具名
    arguments: dict[str, Any] = field(default_factory=dict)  # 工具参数


@dataclass(frozen=True)
class MCPResponse:
    """Response returned from an MCP server to a client."""

    tool_name: str  # 已调用的工具名
    content: str  # 工具返回内容
    is_error: bool = False  # 是否为错误响应
    metadata: dict[str, Any] = field(default_factory=dict)  # 扩展 metadata，供 trace / policy 使用


@dataclass(frozen=True)
class MCPPermissionPolicy:
    """Policy that controls which classes of MCP tools may run."""

    allow_read_only: bool = True
    allow_write: bool = False
    allow_network: bool = False
    allow_destructive: bool = False

    def allows(self, permission_level: str) -> bool:
        """Return whether the policy allows the requested permission level."""

        if permission_level == READ_ONLY_PERMISSION:
            return self.allow_read_only
        if permission_level == WRITE_PERMISSION:
            return self.allow_write
        if permission_level == NETWORK_PERMISSION:
            return self.allow_network
        if permission_level == DESTRUCTIVE_PERMISSION:
            return self.allow_destructive
        return False

    def to_dict(self) -> dict[str, bool]:
        """Render the policy as JSON-ready data."""

        return {
            "allow_read_only": self.allow_read_only,
            "allow_write": self.allow_write,
            "allow_network": self.allow_network,
            "allow_destructive": self.allow_destructive,
        }


@dataclass(frozen=True)
class MCPPermissionDecision:
    """Permission check result for one MCP tool call."""

    tool_name: str
    permission_level: str
    allowed: bool
    reason: str
    next_safe_action: str

    def to_dict(self) -> dict[str, object]:
        """Render the decision as JSON-ready data."""

        return {
            "tool_name": self.tool_name,
            "permission_level": self.permission_level,
            "allowed": self.allowed,
            "reason": self.reason,
            "next_safe_action": self.next_safe_action,
        }
