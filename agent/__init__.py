"""Core package for the Agent learning workspace."""

from .core import AgentRun, WorkspaceAgent
from .events import RuntimeEvent, build_runtime_events
from .llm import DeepSeekConfig, DeepSeekLLMClient, LLMError, LLMMessage, LLMResponse
from .recovery import (
    RecoveryPlan,
    build_exception_recovery_plan,
    build_skill_recovery_plan,
    build_tool_recovery_plan,
    classify_failure,
)
from .router import ToolRoute, route_intent
from .tool_calling import ToolCallSelection, build_tool_calling_messages, parse_tool_call_selection, select_tool_call
from .tool_loop import ToolLoopResult, ToolLoopStep
from .tool_schema import ToolArgumentSpec, ToolSpec, build_workspace_tool_specs
from .tool_synthesis import build_tool_loop_synthesis_messages, synthesize_tool_loop_answer
from .state import AgentStep, AgentState
from .tools import (
    ToolError,
    ToolResult,
    answer_docs_with_llm,
    count_lines,
    list_agent_skills,
    list_dir,
    list_mcp_server_tools,
    list_project_subagents,
    mcp_read_project_file,
    mcp_workspace_summary,
    plan_skill,
    plan_subagent_collaboration,
    read_file,
    run_skill,
    run_skill_with_workspace,
    search_docs,
)

__all__ = [
    "AgentRun",
    "AgentStep",
    "AgentState",
    "DeepSeekConfig",
    "DeepSeekLLMClient",
    "LLMError",
    "LLMMessage",
    "LLMResponse",
    "RecoveryPlan",
    "RuntimeEvent",
    "WorkspaceAgent",
    "ToolRoute",
    "ToolCallSelection",
    "ToolArgumentSpec",
    "ToolLoopResult",
    "ToolLoopStep",
    "ToolSpec",
    "ToolError",
    "ToolResult",
    "build_exception_recovery_plan",
    "build_runtime_events",
    "build_skill_recovery_plan",
    "build_tool_calling_messages",
    "build_tool_loop_synthesis_messages",
    "build_tool_recovery_plan",
    "build_workspace_tool_specs",
    "answer_docs_with_llm",
    "list_agent_skills",
    "list_dir",
    "list_mcp_server_tools",
    "list_project_subagents",
    "mcp_read_project_file",
    "mcp_workspace_summary",
    "plan_skill",
    "plan_subagent_collaboration",
    "read_file",
    "run_skill",
    "run_skill_with_workspace",
    "count_lines",
    "classify_failure",
    "search_docs",
    "parse_tool_call_selection",
    "route_intent",
    "select_tool_call",
    "synthesize_tool_loop_answer",
]
