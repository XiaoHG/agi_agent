"""Small protocol models for local MCP experiments."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class MCPToolSpec:
    """Description of one tool exposed by an MCP server."""

    name: str  # 工具名，client 通过它选择要调用的能力
    description: str  # 工具用途说明
    input_schema: dict[str, Any] = field(default_factory=dict)  # 简化版输入 schema


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
