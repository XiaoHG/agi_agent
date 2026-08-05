"""LLM planner models for LangGraph orchestration."""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

from .llm import DeepSeekLLMClient, LLMError, LLMMessage
from .tool_schema import ToolSpec


@dataclass(frozen=True)
class GraphPlan:
    """Structured plan used by the LangGraph route node."""

    route: str  # graph route name, such as read_file or search_docs
    selected_tool: str  # LangChain tool name executed by the graph
    tool_input: dict[str, str]  # tool arguments passed to the selected tool
    reason: str  # planner reason kept for trace and debugging
    raw_response: str = ""  # raw LLM output, useful when debugging parser issues
    status: str = "llm_planned"  # planner status stored in graph state

    def to_state_update(self) -> dict[str, Any]:
        """Convert the plan to fields expected by the LangGraph state."""

        return {
            "route": self.route,
            "route_reason": self.reason,
            "selected_tool": self.selected_tool,
            "tool_input": self.tool_input,
            "planner_status": self.status,
            "planner_raw_response": self.raw_response,
        }


def build_graph_planner_messages(
    question: str,
    tool_specs: list[ToolSpec],
    prompt: str,
) -> list[LLMMessage]:
    """Build chat messages for the graph planner prompt."""

    catalog = "\n\n".join(spec.to_prompt_block() for spec in tool_specs)
    user_prompt = (
        f"User question:\n{question}\n\n"
        "Available workspace tools:\n"
        f"{catalog}\n\n"
        "Return one JSON object with route, selected_tool, tool_input, and reason."
    )
    return [
        LLMMessage(role="system", content=prompt),
        LLMMessage(role="user", content=user_prompt),
    ]


def plan_graph_route(
    client: DeepSeekLLMClient,
    question: str,
    tool_specs: list[ToolSpec],
    *,
    prompt: str,
) -> GraphPlan:
    """Ask the LLM to produce a validated LangGraph execution plan."""

    response = client.chat(build_graph_planner_messages(question, tool_specs, prompt))
    return parse_graph_plan(response.content)


def parse_graph_plan(raw_response: str) -> GraphPlan:
    """Parse and validate the JSON plan returned by the LLM."""

    payload = _parse_json_object(raw_response)
    route = _read_required_string(payload, "route")
    selected_tool = _read_required_string(payload, "selected_tool")
    reason = _read_required_string(payload, "reason")
    tool_input = payload.get("tool_input")
    if not isinstance(tool_input, dict):
        raise LLMError("Graph planner response must include object tool_input.")

    plan = GraphPlan(
        route=route,
        selected_tool=selected_tool,
        tool_input={str(key): str(value) for key, value in tool_input.items()},
        reason=reason,
        raw_response=raw_response,
    )
    _validate_graph_plan(plan)
    return plan


def _validate_graph_plan(plan: GraphPlan) -> None:
    """Ensure the LLM plan maps to the graph routes this project supports."""

    allowed_tools_by_route = {
        "read_file": "read_workspace_file",
        "search_docs": "search_workspace_docs",
        "answer_docs_with_llm": "answer_workspace_docs_with_llm",
        "skill_execution": "execute_workspace_skill",
    }
    expected_tool = allowed_tools_by_route.get(plan.route)
    if expected_tool is None:
        raise LLMError(f"Unsupported graph planner route: {plan.route}")
    if plan.selected_tool != expected_tool:
        raise LLMError(
            f"Route {plan.route} must select {expected_tool}, got {plan.selected_tool}"
        )
    if plan.route == "read_file" and not plan.tool_input.get("path"):
        raise LLMError("read_file graph plan requires tool_input.path.")
    if plan.route != "read_file" and not plan.tool_input.get("question"):
        raise LLMError(f"{plan.route} graph plan requires tool_input.question.")


def _parse_json_object(raw_response: str) -> dict[str, Any]:
    """Extract one JSON object from an LLM response."""

    text = raw_response.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        raise LLMError("Graph planner response does not contain a JSON object.")
    try:
        decoded = json.loads(text[start : end + 1])
    except json.JSONDecodeError as error:
        raise LLMError("Graph planner response is not valid JSON.") from error
    if not isinstance(decoded, dict):
        raise LLMError("Graph planner response must be a JSON object.")
    return decoded


def _read_required_string(payload: dict[str, Any], key: str) -> str:
    """Read a non-empty string field from parsed planner JSON."""

    value = payload.get(key)
    if not isinstance(value, str) or not value.strip():
        raise LLMError(f"Graph planner response is missing {key}.")
    return value.strip()
