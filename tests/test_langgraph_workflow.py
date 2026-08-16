"""Tests for the LangGraph RAG workflow."""

from pathlib import Path
import tempfile
import unittest

from agent.llm import LLMResponse
from agent.planner import parse_graph_plan, plan_graph_route
from agent.tool_schema import build_workspace_tool_specs
from integrations.langgraph_workflow import build_rag_graph, run_rag_graph


class FakePlannerClient:
    """Test double that returns a fixed planner response."""

    def __init__(self, content: str) -> None:
        """Initialize the instance state needed by this object."""
        self.content = content

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature loose
        """Return a deterministic chat response used by the surrounding test or fake client."""
        return LLMResponse(model="fake", content=self.content, raw={"messages": len(messages)})


class FakeToolCallingClient:
    """Test double that returns a fixed tool-calling response."""

    def __init__(self, content: str) -> None:
        """Initialize the instance state needed by this object."""
        self.content = content

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature loose
        """Return a deterministic chat response used by the surrounding test or fake client."""
        return LLMResponse(model="fake", content=self.content, raw={"messages": len(messages)})


class SequenceToolLoopClient:
    """Test double that returns one tool-loop response per call."""

    def __init__(self, responses: list[str]) -> None:
        """Initialize the instance state needed by this object."""
        self.responses = responses
        self.calls = 0

    def chat(self, messages):  # noqa: ANN001 - test double keeps the signature loose
        """Return a deterministic chat response used by the surrounding test or fake client."""
        response = self.responses[min(self.calls, len(self.responses) - 1)]
        self.calls += 1
        return LLMResponse(model="fake", content=response, raw={"messages": len(messages)})


class LangGraphWorkflowTests(unittest.TestCase):
    """Verify the minimal LangGraph workflow runs through expected graph nodes."""

    def test_build_rag_graph_returns_invokable_graph(self) -> None:
        """Verify that build rag graph returns invokable graph."""
        graph = build_rag_graph(Path("."))

        self.assertTrue(hasattr(graph, "invoke"))

    def test_rag_graph_handles_no_context_without_network(self) -> None:
        """Verify that rag graph handles no context without network."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "the and of")

            self.assertEqual(result["route"], "answer_docs_with_llm")
            self.assertEqual(result["selected_tool"], "answer_workspace_docs_with_llm")
            self.assertEqual(result["steps"], ["route", "call_tool", "finalize"])
            self.assertIn("insufficient", result["answer"])
            self.assertNotIn("error", result)

    def test_rag_graph_routes_to_search_docs(self) -> None:
        """Verify that rag graph routes to search docs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Search docs for agent workflow.")

            self.assertEqual(result["route"], "search_docs")
            self.assertEqual(result["selected_tool"], "search_workspace_docs")
            self.assertIn("relevant local context", result["answer"])

    def test_rag_graph_routes_to_read_file(self) -> None:
        """Verify that rag graph routes to read file."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Read README.md.")

            self.assertEqual(result["route"], "read_file")
            self.assertEqual(result["selected_tool"], "read_workspace_file")
            self.assertIn("[read_file] README.md", result["answer"])

    def test_rag_graph_route_hint_direct_answer_uses_llm_when_available(self) -> None:
        """Verify that rag graph route hint direct answer uses llm when available."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = FakePlannerClient("LLM answer: agents can plan and use tools.")

            result = run_rag_graph(
                root,
                "Explain the difference between an agent and a chatbot.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="direct_answer",
            )

            self.assertEqual(result["route"], "direct_answer")
            self.assertEqual(result["steps"], ["route", "finalize"])
            self.assertEqual(result["direct_answer"]["source"], "llm")
            self.assertEqual(result["direct_answer"]["status"], "completed")
            self.assertIn("LLM answer:", result["answer"])

    def test_rag_graph_recovers_failed_tool_call(self) -> None:
        """Verify that rag graph recovers failed tool call."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = run_rag_graph(root, "Read missing.md.")

            self.assertEqual(result["route"], "read_file")
            self.assertEqual(result["tool_status"], "failed")
            self.assertEqual(result["steps"], ["route", "call_tool", "recover_tool_failure", "finalize"])
            self.assertEqual(result["recovery_plan"]["source_type"], "tool")
            self.assertEqual(result["recovery_plan"]["source_name"], "read_workspace_file")
            self.assertEqual(result["recovery_plan"]["tool_name"], "read_workspace_file")
            self.assertEqual(result["recovery_plan"]["failure_type"], "missing_resource")
            self.assertIn("Tool recovery plan", result["answer"])

    def test_rag_graph_executes_workflow_steps_inside_graph(self) -> None:
        """Verify that rag graph executes workflow steps inside graph."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\nrag retrieval\n", encoding="utf-8")

            result = run_rag_graph(root, "Read README.md and then count lines.", route_hint_action="workflow")

            self.assertEqual(result["route"], "workflow_execution")
            self.assertEqual(result["workflow_status"], "completed")
            self.assertEqual(
                result["steps"],
                [
                    "route",
                    "build_workflow",
                    "run_workflow_step",
                    "run_workflow_step",
                    "finalize_workflow",
                    "finalize",
                ],
            )
            self.assertIn("workflow completed", result["answer"])
            self.assertIn("count_lines", result["answer"])

    def test_rag_graph_workflow_failure_stops_remaining_steps(self) -> None:
        """Verify that rag graph workflow failure stops remaining steps."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = run_rag_graph(root, "Read missing.md and then count lines.", route_hint_action="workflow")

            self.assertEqual(result["route"], "workflow_execution")
            self.assertEqual(result["workflow_status"], "failed")
            self.assertEqual(
                result["steps"],
                [
                    "route",
                    "build_workflow",
                    "run_workflow_step",
                    "finalize_workflow",
                    "finalize",
                ],
            )
            self.assertEqual(result["recovery_plan"]["tool_name"], "read_workspace_file")
            self.assertIn("workflow failed", result["answer"])

    def test_rag_graph_runs_tool_call_selection_then_tool(self) -> None:
        """Verify that rag graph runs tool call selection then tool."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = FakeToolCallingClient(
                '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the requested file."}'
            )

            result = run_rag_graph(root, "Use tool calling to read README.md.", planner_client=client, route_hint_action="tool_call", route_hint_tool_input="read README.md")  # type: ignore[arg-type]

            self.assertEqual(result["route"], "tool_call_execution")
            self.assertEqual(result["tool_call_status"], "ready_to_execute")
            self.assertEqual(result["logical_tool_name"], "read_file")
            self.assertEqual(result["selected_tool"], "read_workspace_file")
            self.assertEqual(result["steps"], ["route", "select_tool_call", "call_tool", "finalize"])
            self.assertIn("[read_file] README.md", result["answer"])

    def test_rag_graph_runs_tool_call_direct_answer(self) -> None:
        """Verify that rag graph runs tool call direct answer."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = FakeToolCallingClient(
                '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"The request can be answered directly."}'
            )

            result = run_rag_graph(
                root,
                "Use tool calling to explain the difference between an agent and a chatbot.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="tool_call",
                route_hint_tool_input="explain the difference between an agent and a chatbot",
            )

            self.assertEqual(result["route"], "tool_call_execution")
            self.assertEqual(result["tool_call_status"], "answer_directly")
            self.assertEqual(result["steps"], ["route", "select_tool_call", "finalize"])
            self.assertIn("main difference", result["answer"])

    def test_rag_graph_runs_tool_call_clarification(self) -> None:
        """Verify that rag graph runs tool call clarification."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            client = FakeToolCallingClient(
                '{"action":"ask_clarification","tool_name":null,"tool_input":null,"reason":"The target file is missing."}'
            )

            result = run_rag_graph(
                root,
                "Use tool calling to inspect a file.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="tool_call",
                route_hint_tool_input="inspect a file",
            )

            self.assertEqual(result["route"], "tool_call_execution")
            self.assertEqual(result["tool_call_status"], "needs_clarification")
            self.assertEqual(result["steps"], ["route", "select_tool_call", "finalize"])
            self.assertIn("needs more information", result["answer"])

    def test_rag_graph_runs_tool_loop_inside_graph(self) -> None:
        """Verify that rag graph runs tool loop inside graph."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = SequenceToolLoopClient(
                [
                    '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the README first."}',
                    '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"The README observation is enough."}',
                    "The README was read successfully, so the tool loop has enough evidence to answer.",
                ]
            )

            result = run_rag_graph(
                root,
                "Use tool loop to read README.md and then answer.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="tool_loop",
                route_hint_tool_input="read README.md and then answer",
            )

            self.assertEqual(result["route"], "tool_loop_execution")
            self.assertEqual(result["tool_loop_result"]["stop_reason"], "model_answered_directly")
            self.assertEqual(result["tool_loop_result"]["final_answer_source"], "llm")
            self.assertEqual(
                result["steps"],
                [
                    "route",
                    "initialize_tool_loop",
                    "run_tool_loop_iteration",
                    "run_tool_loop_iteration",
                    "synthesize_tool_loop",
                    "finalize_tool_loop",
                    "finalize",
                ],
            )
            self.assertIn("The README was read successfully", result["answer"])

    def test_rag_graph_tool_loop_stops_on_repeated_tool_call(self) -> None:
        """Verify that rag graph tool loop stops on repeated tool call."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = SequenceToolLoopClient(
                [
                    '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the file."}',
                    '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the same file again."}',
                    "The loop stopped because the model repeated the same read_file call.",
                ]
            )

            result = run_rag_graph(
                root,
                "Use tool loop to read README.md and then answer.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="tool_loop",
                route_hint_tool_input="read README.md and then answer",
            )

            self.assertEqual(result["route"], "tool_loop_execution")
            self.assertEqual(result["tool_loop_result"]["stop_reason"], "repeated_tool_call")
            self.assertEqual(result["tool_loop_result"]["final_answer_source"], "llm")
            self.assertIn("repeated the same read_file call", result["answer"])

    def test_rag_graph_tool_loop_keeps_deterministic_fallback_when_synthesis_fails(self) -> None:
        """Verify that rag graph tool loop keeps deterministic fallback when synthesis fails."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = SequenceToolLoopClient(
                [
                    '{"action":"use_tool","tool_name":"count_lines","tool_input":"README.md","reason":"Count the README lines."}',
                    '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"Line count is enough."}',
                    "",
                ]
            )

            result = run_rag_graph(
                root,
                "Use tool loop to count lines in README.md and answer.",
                planner_client=client,  # type: ignore[arg-type]
                route_hint_action="tool_loop",
                route_hint_tool_input="count lines in README.md and answer",
            )

            self.assertEqual(result["route"], "tool_loop_execution")
            self.assertEqual(result["tool_loop_result"]["final_answer_source"], "deterministic_fallback")
            self.assertIn("Final synthesis fallback reason", result["answer"])

    def test_rag_graph_tool_status_controls_next_edge(self) -> None:
        """Verify that rag graph tool status controls next edge."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Read README.md.")

            self.assertEqual(result["tool_status"], "completed")
            self.assertEqual(result["steps"], ["route", "call_tool", "finalize"])
            self.assertNotIn("recovery_plan", result)

    def test_rag_graph_routes_to_skill_execution(self) -> None:
        """Verify that rag graph routes to skill execution."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Execute skill for code review.")

            self.assertEqual(result["route"], "skill_execution")
            self.assertEqual(result["selected_tool"], "execute_workspace_skill")
            self.assertEqual(result["skill_status"], "completed")
            self.assertEqual(result["steps"], ["route", "call_skill", "finalize"])
            self.assertIn("Skill run: code_review", result["answer"])

    def test_rag_graph_executes_subagent_runtime_and_keeps_session(self) -> None:
        """Verify that rag graph executes subagent runtime and keeps session."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(
                root,
                "Execute subagent collaboration for a code review.",
                route_hint_action="use_tool",
                route_hint_tool_name="execute_subagents",
                route_hint_tool_input="Execute subagent collaboration for a code review.",
            )

            self.assertEqual(result["route"], "execute_subagents")
            self.assertEqual(result["selected_tool"], "execute_workspace_subagents")
            self.assertEqual(result["tool_status"], "completed")
            self.assertEqual(result["subagent_runtime"]["status"], "completed")
            self.assertIn("session_id", result["subagent_runtime"])
            self.assertGreaterEqual(len(result["subagent_runtime"]["transitions"]), 1)

    def test_rag_graph_keeps_skill_run_trace(self) -> None:
        """Verify that rag graph keeps skill run trace."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Run skill for code review.")

            skill_run = result["skill_run"]
            self.assertEqual(skill_run["skill"]["name"], "code_review")
            self.assertEqual(skill_run["status"], "completed")
            self.assertGreaterEqual(skill_run["tool_backed_steps"], 1)
            self.assertGreaterEqual(skill_run["step_count"], 1)

    def test_rag_graph_skill_status_controls_next_edge(self) -> None:
        """Verify that rag graph skill status controls next edge."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Use skill for code review.")

            self.assertEqual(result["skill_status"], "completed")
            self.assertEqual(result["steps"][-1], "finalize")
            self.assertNotIn("error", result)

    def test_rag_graph_recovers_failed_skill_run(self) -> None:
        """Verify that rag graph recovers failed skill run."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Use skill for learning explanation.")

            self.assertEqual(result["skill_status"], "failed")
            self.assertEqual(result["steps"], ["route", "call_skill", "recover_skill_failure", "finalize"])
            self.assertEqual(result["recovery_plan"]["source_type"], "skill")
            self.assertEqual(result["recovery_plan"]["source_name"], "learning_explanation")
            self.assertEqual(result["recovery_plan"]["skill_name"], "learning_explanation")
            self.assertIn("docs/current-learning-state.md", result["recovery_plan"]["reason"])
            self.assertIn("Skill recovery plan", result["answer"])

    def test_rag_graph_records_route_reason(self) -> None:
        """Verify that rag graph records route reason."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Search docs for agent workflow.")

            self.assertIn("route_reason", result)
            self.assertIn("local context", result["route_reason"])

    def test_parse_graph_plan_validates_llm_json(self) -> None:
        """Verify that parse graph plan validates llm json."""
        plan = parse_graph_plan(
            '{"route":"read_file","selected_tool":"read_workspace_file","tool_input":{"path":"README.md"},"reason":"Read the requested file."}'
        )

        self.assertEqual(plan.route, "read_file")
        self.assertEqual(plan.selected_tool, "read_workspace_file")
        self.assertEqual(plan.tool_input["path"], "README.md")

    def test_plan_graph_route_uses_tool_catalog(self) -> None:
        """Verify that plan graph route uses tool catalog."""
        client = FakePlannerClient(
            '{"route":"search_docs","selected_tool":"search_workspace_docs","tool_input":{"question":"agent workflow"},"reason":"Search local docs."}'
        )

        plan = plan_graph_route(
            client,  # type: ignore[arg-type]
            "Find docs about agent workflow.",
            build_workspace_tool_specs(),
            prompt="Planner prompt",
        )

        self.assertEqual(plan.route, "search_docs")
        self.assertEqual(plan.status, "llm_planned")

    def test_rag_graph_uses_llm_planner_when_available(self) -> None:
        """Verify that rag graph uses llm planner when available."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = FakePlannerClient(
                '{"route":"read_file","selected_tool":"read_workspace_file","tool_input":{"path":"README.md"},"reason":"The planner selected file reading."}'
            )

            result = run_rag_graph(root, "Inspect the main project file.", planner_client=client)  # type: ignore[arg-type]

            self.assertEqual(result["planner_status"], "llm_planned")
            self.assertEqual(result["route"], "read_file")
            self.assertEqual(result["selected_tool"], "read_workspace_file")
            self.assertIn("[read_file] README.md", result["answer"])

    def test_rag_graph_falls_back_when_llm_planner_fails(self) -> None:
        """Verify that rag graph falls back when llm planner fails."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            client = FakePlannerClient("not json")

            result = run_rag_graph(root, "Search docs for agent workflow.", planner_client=client)  # type: ignore[arg-type]

            self.assertEqual(result["planner_status"], "deterministic_fallback")
            self.assertIn("planner_error", result)
            self.assertEqual(result["route"], "search_docs")
            self.assertEqual(result["selected_tool"], "search_workspace_docs")


if __name__ == "__main__":
    unittest.main()
