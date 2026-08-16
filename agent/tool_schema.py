"""Workspace tool schema definitions used for LLM tool selection."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ToolArgumentSpec:
    """Describe one argument accepted by a workspace tool."""

    name: str               # 参数名，如 path、question、task
    type_name: str          # 参数类型：string
    description: str        # 参数说明
    required: bool = True   # 是否必填


@dataclass(frozen=True)
class ToolSpec:
    """Describe one workspace tool in a model-readable format."""

    name: str              # 工具名：read_file、search_docs 等
    description: str       # 工具功能说明
    arguments: tuple[ToolArgumentSpec, ...] = ()  # 参数列表

    def to_prompt_block(self) -> str:
        """Render the tool as a compact instruction block for the LLM."""

        if not self.arguments:
            return f"- {self.name}: {self.description}\n  arguments: none"

        argument_lines = []
        for argument in self.arguments:
            requirement = "required" if argument.required else "optional"
            argument_lines.append(
                f"  - {argument.name} ({argument.type_name}, {requirement}): {argument.description}"
            )
        return f"- {self.name}: {self.description}\n" + "\n".join(argument_lines)


def build_workspace_tool_specs() -> list[ToolSpec]:
    """Return the curated tool catalog used by the tool-calling prompt."""

    return [
        ToolSpec(
            name="read_file",
            description="Read a small text file from the workspace root.",
            arguments=(ToolArgumentSpec("path", "string", "Workspace-relative file path."),),
        ),
        ToolSpec(
            name="list_dir",
            description="List files and directories inside the workspace root.",
            arguments=(ToolArgumentSpec("path", "string", "Workspace-relative directory path.", required=False),),
        ),
        ToolSpec(
            name="count_lines",
            description="Count the number of lines in a workspace file.",
            arguments=(ToolArgumentSpec("path", "string", "Workspace-relative file path."),),
        ),
        ToolSpec(
            name="search_docs",
            description="Search local project documents and return relevant context chunks.",
            arguments=(ToolArgumentSpec("question", "string", "Natural-language search question."),),
        ),
        ToolSpec(
            name="search_vector_docs",
            description="Search local project documents through the professional RAG vector index.",
            arguments=(ToolArgumentSpec("question", "string", "Natural-language semantic search question."),),
        ),
        ToolSpec(
            name="answer_docs_with_llm",
            description="Answer from local project documents with DeepSeek-grounded RAG.",
            arguments=(ToolArgumentSpec("question", "string", "Natural-language grounded question."),),
        ),
        ToolSpec(
            name="list_mcp_tools",
            description="List local MCP tools exposed by the workspace.",
        ),
        ToolSpec(
            name="mcp_workspace_summary",
            description="Summarize the workspace through the local MCP adapter.",
        ),
        ToolSpec(
            name="mcp_read_project_file",
            description="Read a workspace file through the local MCP adapter.",
            arguments=(ToolArgumentSpec("path", "string", "Workspace-relative file path."),),
        ),
        ToolSpec(
            name="mcp_write_project_file",
            description="Write a workspace file through the local MCP adapter. This may be denied by the MCP permission policy.",
            arguments=(ToolArgumentSpec("task", "string", "Natural-language write request containing path and content."),),
        ),
        ToolSpec(
            name="list_skills",
            description="List reusable skills available in the project.",
        ),
        ToolSpec(
            name="plan_skill",
            description="Select a reusable skill for a task.",
            arguments=(ToolArgumentSpec("task", "string", "Task description."),),
        ),
        ToolSpec(
            name="execute_skill",
            description="Execute the best reusable skill for a task and return a structured skill run.",
            arguments=(ToolArgumentSpec("task", "string", "Task description."),),
        ),
        ToolSpec(
            name="list_subagents",
            description="List project subagents.",
        ),
        ToolSpec(
            name="plan_subagents",
            description="Plan subagent collaboration for a task.",
            arguments=(ToolArgumentSpec("task", "string", "Task description."),),
        ),
        ToolSpec(
            name="execute_subagents",
            description="Execute the subagent runtime foundation and return structured delegation, runtime-session, and recovery evidence.",
            arguments=(ToolArgumentSpec("task", "string", "Task description."),),
        ),
    ]
