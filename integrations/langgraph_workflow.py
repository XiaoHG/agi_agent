"""LangGraph workflows for the workspace agent project."""

from __future__ import annotations

from pathlib import Path
from typing import TypedDict

from langgraph.graph import END, START, StateGraph

from .langchain_tools import build_langchain_tools


class RAGGraphState(TypedDict, total=False):
    """State passed between LangGraph nodes for the RAG workflow."""
    question: str           # 用户问题
    selected_tool: str      # 选哪个工具
    tool_output: str        # 工具返回结果
    answer: str             # 最终回答
    error: str              # 错误信息
    steps: list[str]        # 执行步骤记录（调试用）


def build_rag_graph(workspace_root: Path | str = "."):
    """Build a minimal LangGraph workflow for DeepSeek-grounded RAG."""

    root = Path(workspace_root).resolve()  # 固定 graph 工作区根目录
    tools = {tool.name: tool for tool in build_langchain_tools(root)}

    def prepare(state: RAGGraphState) -> RAGGraphState:
        """Select the LangChain tool for the current graph run."""

        steps = [*state.get("steps", []), "prepare"]
        return {
            **state,
            "selected_tool": "answer_workspace_docs_with_llm",
            "steps": steps,
        }

    def call_tool(state: RAGGraphState) -> RAGGraphState:
        """Invoke the selected LangChain tool and store the output."""

        steps = [*state.get("steps", []), "call_tool"]
        tool_name = state["selected_tool"]
        tool = tools[tool_name]
        try:
            output = tool.invoke({"question": state["question"]})
            return {
                **state,
                "tool_output": output,
                "steps": steps,
            }
        except Exception as error:
            return {
                **state,
                "error": str(error),
                "steps": steps,
            }

    def finalize(state: RAGGraphState) -> RAGGraphState:
        """Convert tool output or error into the final graph answer."""

        steps = [*state.get("steps", []), "finalize"]
        if state.get("error"):
            return {
                **state,
                "answer": f"Graph failed: {state['error']}",
                "steps": steps,
            }
        return {
            **state,
            "answer": state.get("tool_output", ""),
            "steps": steps,
        }

    graph = StateGraph(RAGGraphState)
    graph.add_node("prepare", prepare)
    graph.add_node("call_tool", call_tool)
    graph.add_node("finalize", finalize)
    graph.add_edge(START, "prepare")
    graph.add_edge("prepare", "call_tool")
    graph.add_edge("call_tool", "finalize")
    graph.add_edge("finalize", END)
    return graph.compile()


def run_rag_graph(workspace_root: Path | str, question: str) -> RAGGraphState:
    """Run the minimal LangGraph RAG workflow."""

    graph = build_rag_graph(workspace_root)
    return graph.invoke({"question": question, "steps": []})
