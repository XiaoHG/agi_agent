"""LangChain tool adapters for the workspace agent core tools."""

from __future__ import annotations

from pathlib import Path

from langchain_core.tools import StructuredTool
from pydantic import BaseModel, Field

from agent import (
    answer_docs_with_llm,
    count_lines,
    list_agent_skills,
    list_dir,
    list_mcp_server_tools,
    list_project_subagents,
    mcp_workspace_summary,
    plan_skill,
    plan_subagent_collaboration,
    read_file,
    search_docs,
)


class PathInput(BaseModel):
    """Input schema for tools that operate on a workspace-relative path."""

    path: str = Field(default=".", description="Workspace-relative file or directory path.")


class QuestionInput(BaseModel):
    """Input schema for tools that answer or search with a natural-language question."""

    question: str = Field(description="Natural-language question or task.")


class EmptyInput(BaseModel):
    """Input schema for tools that do not need user arguments."""


def build_langchain_tools(workspace_root: Path | str = ".") -> list[StructuredTool]:
    """Build real LangChain StructuredTool adapters for local project tools."""

    root = Path(workspace_root).resolve()  # 适配层固定工作区根目录，避免每个工具重复解析路径

    def read_workspace_file(path: str = ".") -> str:
        """Read a text file from the workspace."""

        return read_file(root, path).output

    def list_workspace_directory(path: str = ".") -> str:
        """List a directory inside the workspace."""

        return list_dir(root, path).output

    def count_workspace_file_lines(path: str = ".") -> str:
        """Count lines in a workspace file."""

        return count_lines(root, path).output

    def search_workspace_docs(question: str) -> str:
        """Search local project documents and return matching context chunks."""

        return search_docs(root, question).output

    def answer_workspace_docs_with_llm(question: str) -> str:
        """Answer from local project documents with DeepSeek-grounded RAG."""

        return answer_docs_with_llm(root, question).output

    def list_workspace_mcp_tools() -> str:
        """List local MCP tools available in the workspace."""

        return list_mcp_server_tools(root).output

    def summarize_workspace_with_mcp() -> str:
        """Summarize the workspace through the local MCP adapter."""

        return mcp_workspace_summary(root).output

    def list_workspace_skills() -> str:
        """List reusable project skills."""

        return list_agent_skills().output

    def plan_workspace_skill(question: str) -> str:
        """Select a reusable skill for a task."""

        return plan_skill(question).output

    def list_workspace_subagents() -> str:
        """List project subagents."""

        return list_project_subagents().output

    def plan_workspace_subagents(question: str) -> str:
        """Plan subagent collaboration for a task."""

        return plan_subagent_collaboration(question).output

    return [
        StructuredTool.from_function(
            func=read_workspace_file,
            name="read_workspace_file",
            description="Read a small text file from the workspace.",
            args_schema=PathInput,
        ),
        StructuredTool.from_function(
            func=list_workspace_directory,
            name="list_workspace_directory",
            description="List files and directories inside the workspace.",
            args_schema=PathInput,
        ),
        StructuredTool.from_function(
            func=count_workspace_file_lines,
            name="count_workspace_file_lines",
            description="Count lines in a workspace file.",
            args_schema=PathInput,
        ),
        StructuredTool.from_function(
            func=search_workspace_docs,
            name="search_workspace_docs",
            description="Search local project documents and return relevant context chunks.",
            args_schema=QuestionInput,
        ),
        StructuredTool.from_function(
            func=answer_workspace_docs_with_llm,
            name="answer_workspace_docs_with_llm",
            description="Answer from local project documents with DeepSeek-grounded RAG.",
            args_schema=QuestionInput,
            metadata={"requires_network": True, "requires_api_key": "DEEPSEEK_API_KEY"},
        ),
        StructuredTool.from_function(
            func=list_workspace_mcp_tools,
            name="list_workspace_mcp_tools",
            description="List local MCP tools exposed by the workspace.",
            args_schema=EmptyInput,
        ),
        StructuredTool.from_function(
            func=summarize_workspace_with_mcp,
            name="summarize_workspace_with_mcp",
            description="Summarize the workspace through the local MCP adapter.",
            args_schema=EmptyInput,
        ),
        StructuredTool.from_function(
            func=list_workspace_skills,
            name="list_workspace_skills",
            description="List reusable skills available in the project.",
            args_schema=EmptyInput,
        ),
        StructuredTool.from_function(
            func=plan_workspace_skill,
            name="plan_workspace_skill",
            description="Select a reusable skill for a task.",
            args_schema=QuestionInput,
        ),
        StructuredTool.from_function(
            func=list_workspace_subagents,
            name="list_workspace_subagents",
            description="List project subagents.",
            args_schema=EmptyInput,
        ),
        StructuredTool.from_function(
            func=plan_workspace_subagents,
            name="plan_workspace_subagents",
            description="Plan project subagent collaboration for a task.",
            args_schema=QuestionInput,
        ),
    ]
