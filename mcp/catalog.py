"""External MCP catalog loading helpers."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
from typing import Any

from .schema import MCPToolSpec


DEFAULT_MCP_CATALOG_PATH = Path("configs/mcp-catalog.json")
MCP_CATALOG_ENV_VAR = "AGI_AGENT_MCP_CATALOG_PATH"


@dataclass(frozen=True)
class CatalogedMCPTool:
    """One external MCP tool entry resolved from a catalog file."""

    spec: MCPToolSpec               # MCP协议标准工具定义：名字、描述、入参schema、权限等级
    response_template: str|None     # 【业务扩展】工具执行完成后，返回给Agent的回复模板，用来统一格式化输出
    source_path: str|None           # 记录这个工具来自哪个json配置文件，用于追踪来源、排查问题

    def to_dict(self) -> dict[str, Any]:
        """Render the catalog entry as JSON-ready data."""

        return {
            "spec": {
                "name": self.spec.name,
                "description": self.spec.description,
                "input_schema": self.spec.input_schema,
                "permission_level": self.spec.permission_level,
            },
            "response_template": self.response_template,
            "source_path": self.source_path,
        }


@dataclass(frozen=True)
class MCPCatalogSource:
    """One resolved source used to build the merged MCP catalog."""

    name: str                               # 来源名称：builtin / external
    path: str|None                          # 配置文件路径；builtin没有文件，为None
    loaded_tool_names: tuple[str, ...]      # 该来源加载到的全部工具名列表

    def to_dict(self) -> dict[str, Any]:
        """Render the catalog source as JSON-ready data."""

        return {
            "name": self.name,
            "path": self.path,
            "loaded_tool_names": list(self.loaded_tool_names),
        }


def get_mcp_catalog_path(root: Path = Path("."), env: dict[str, str] | None = None) -> Path:
    """Return the external MCP catalog path from env or the default config."""

    resolved_env = env or os.environ
    raw_path = resolved_env.get(MCP_CATALOG_ENV_VAR, "").strip()
    if raw_path:
        return Path(raw_path)
    return root / DEFAULT_MCP_CATALOG_PATH


def load_external_mcp_catalog(
    root: Path = Path("."),
    *,
    env: dict[str, str] | None = None,
    catalog_path: Path | str | None = None,
) -> list[CatalogedMCPTool]:
    """Load external MCP tool definitions from a JSON catalog file."""

    resolved_path = Path(catalog_path) if catalog_path is not None else get_mcp_catalog_path(root, env=env)
    if not resolved_path.exists():
        return []
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        return []
    records = payload.get("tools", [])
    if not isinstance(records, list):
        return []

    tools: list[CatalogedMCPTool] = []
    for record in records:
        if not isinstance(record, dict):
            continue
        name = str(record.get("name", "")).strip()
        description = str(record.get("description", "")).strip()
        if not name or not description:
            continue
        input_schema = record.get("input_schema", {})
        if not isinstance(input_schema, dict):
            input_schema = {}
        permission_level = str(record.get("permission_level", "read_only")).strip() or "read_only"
        response_template = record.get("response_template")
        tools.append(
            CatalogedMCPTool(
                spec=MCPToolSpec(
                    name=name,
                    description=description,
                    input_schema=input_schema,
                    permission_level=permission_level,
                ),
                response_template=str(response_template).strip() if isinstance(response_template, str) and response_template.strip() else None,
                source_path=str(resolved_path),
            )
        )
    return tools


def build_mcp_catalog_sources(root: Path = Path("."), env: dict[str, str] | None = None) -> tuple[MCPCatalogSource, ...]:
    """Build a compact summary of MCP catalog sources used by the server."""

    external_tools = load_external_mcp_catalog(root, env=env)
    catalog_path = get_mcp_catalog_path(root, env=env)
    return (
        MCPCatalogSource(name="builtin", path=None, loaded_tool_names=tuple()),
        MCPCatalogSource(name="external", path=str(catalog_path), loaded_tool_names=tuple(tool.spec.name for tool in external_tools)),
    )
