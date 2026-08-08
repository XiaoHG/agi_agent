"""Tests for the minimal workspace agent."""

from pathlib import Path
import tempfile  # 临时文件夹，测试完自动删，不污染环境
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, count_lines, list_dir, read_file, route_intent
from agent.llm import LLMError, LLMResponse


class WorkspaceAgentTests(unittest.TestCase):
    """Verify routing, tools, and user-facing behaviors."""

    def test_route_to_read_file(self) -> None:
        route = route_intent("Read README.md and summarize the project learning goals.")
        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "read_file")
        self.assertEqual(route.tool_input, "README.md")

    def test_route_to_list_dir(self) -> None:
        route = route_intent("List the main project directories and explain what they are responsible for.")
        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_dir")

    def test_route_to_file_count_lines(self) -> None:
        text = "Count lines in README.md."
        route = route_intent(text)
        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "count_lines")
        self.assertEqual(route.tool_input, "README.md")

    def test_route_to_workflow(self) -> None:
        text = "Read README.md and then count lines."
        route = route_intent(text)
        self.assertEqual(route.action, "workflow")

    def test_route_to_langgraph(self) -> None:
        route = route_intent("Use LangGraph to search docs for MCP.")

        self.assertEqual(route.action, "graph")
        self.assertEqual(route.tool_name, "langgraph_workflow")
        self.assertEqual(route.tool_input, "search docs for MCP")

    def test_route_to_tool_calling(self) -> None:
        route = route_intent("Use tool calling to read README.md.")

        self.assertEqual(route.action, "tool_call")
        self.assertEqual(route.tool_name, "llm_tool_selector")
        self.assertEqual(route.tool_input, "read README.md")

    def test_route_to_tool_loop(self) -> None:
        route = route_intent("Use tool loop to read README.md and then answer.")

        self.assertEqual(route.action, "tool_loop")
        self.assertEqual(route.tool_name, "llm_tool_loop")
        self.assertEqual(route.tool_input, "read README.md and then answer")

    def test_workflow_run(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Read README.md and then count lines.")
        self.assertIn("workflow completed", run.answer)
        self.assertIn("count_lines", run.answer)
        self.assertTrue(any(step.title == "Run workflow graph" for step in run.steps))

    def test_workflow_lists_directories_then_reads_readme(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("List directories and then read README.md.")
        self.assertIn("workflow completed", run.answer)
        self.assertIn("configs", run.answer)
        self.assertIn("agi_agent", run.answer)
        self.assertEqual(run.tool_result.tool_name if run.tool_result else None, "workflow")
        self.assertEqual((run.tool_result.metadata or {}).get("graph_route") if run.tool_result else None, "workflow_execution")

    def test_workflow_stops_after_missing_file_error(self) -> None:
        agent = WorkspaceAgent(Path("."))
        text = "Read not-exist.md and then count lines."
        route = route_intent(text)
        self.assertEqual(route.action, "workflow")
        run = agent.run(text)
        self.assertIn("workflow failed", run.answer)
        self.assertIn("File does not exist", run.answer)
        self.assertEqual(run.tool_result.tool_name if run.tool_result else None, "workflow")
        self.assertTrue(any(step.title == "Run workflow graph" for step in run.steps))
        self.assertEqual((run.tool_result.metadata or {}).get("tool_status") if run.tool_result else None, "failed")

    def test_workflow_can_opt_out_of_graph_runtime(self) -> None:
        agent = WorkspaceAgent(Path("."), use_graph_runtime=False)

        run = agent.run("Read README.md and then count lines.")

        self.assertIn("workflow completed", run.answer)
        self.assertFalse(any(step.title == "Run workflow graph" for step in run.steps))
        self.assertTrue(any(step.title == "Build workflow" for step in run.steps))

    def test_read_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "demo.txt").write_text("hello\nworld\n", encoding="utf-8")
            result = read_file(root, "demo.txt")
            self.assertEqual(result.tool_name, "read_file")
            self.assertIn("hello", result.output)

    def test_list_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "a.txt").write_text("x", encoding="utf-8")
            (root / "dir").mkdir()
            result = list_dir(root, ".")
            self.assertIn("- a.txt", result.output)
            self.assertIn("- dir/", result.output)

    def test_agent_direct_answer(self) -> None:
        class FailingDirectAnswerClient:
            def chat(self, messages):  # noqa: ANN001
                raise LLMError("Direct answer model unavailable.")

        agent = WorkspaceAgent(Path("."), llm_client=FailingDirectAnswerClient())
        run = agent.run("Explain the difference between an agent and a chatbot.")
        self.assertIn("main difference", run.answer)
        self.assertEqual(run.route.action, "direct_answer")
        self.assertTrue(any(step.title == "Run graph runtime" for step in run.steps))

    def test_agent_direct_answer_uses_llm_when_available(self) -> None:
        class FakeDirectAnswerClient:
            def chat(self, messages):  # noqa: ANN001
                return LLMResponse(
                    model="fake",
                    content="LLM answer: an agent can plan, call tools, and keep execution state.",
                    raw={"messages": len(messages)},
                )

        agent = WorkspaceAgent(Path("."), llm_client=FakeDirectAnswerClient())

        run = agent.run("Explain the difference between an agent and a chatbot.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.action, "direct_answer")
        self.assertIn("LLM answer:", run.answer)
        self.assertEqual(trace["direct_answer"]["source"], "llm")
        self.assertEqual(trace["direct_answer"]["status"], "completed")

    def test_agent_direct_answer_keeps_deterministic_fallback_when_llm_fails(self) -> None:
        class FailingDirectAnswerClient:
            def chat(self, messages):  # noqa: ANN001
                raise LLMError("Direct answer model unavailable.")

        agent = WorkspaceAgent(Path("."), llm_client=FailingDirectAnswerClient())

        run = agent.run("Explain the difference between an agent and a chatbot.")
        trace = agent.to_trace_dict(run)

        self.assertIn("main difference", run.answer)
        self.assertEqual(trace["direct_answer"]["source"], "deterministic_fallback")
        self.assertEqual(trace["direct_answer"]["status"], "fallback")
        self.assertIn("unavailable", trace["direct_answer"]["error"])

    def test_agent_handles_missing_file(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Read not-exist.md.")
        self.assertIn("tool call failed", run.answer)
        self.assertIn("File does not exist", run.tool_error or "")

    def test_agent_summarizes_readme_learning_goals(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Read README.md and summarize the project learning goals.")
        self.assertIn("Result: read README.md", run.answer)
        self.assertIn("agi_agent", run.answer)
        self.assertEqual(run.tool_result.tool_name if run.tool_result else None, "read_file")
        self.assertEqual((run.tool_result.metadata or {}).get("graph_route") if run.tool_result else None, "read_file")

    def test_agent_can_opt_out_of_default_graph_runtime(self) -> None:
        agent = WorkspaceAgent(Path("."), use_graph_runtime=False)

        run = agent.run("Read README.md and summarize the project learning goals.")

        self.assertIn("Result: read README.md", run.answer)
        self.assertFalse(any(step.title == "Run graph runtime" for step in run.steps))

    def test_agent_tool_call_runs_through_default_graph_runtime(self) -> None:
        class FakeToolCallingClient:
            def chat(self, messages):  # noqa: ANN001
                return LLMResponse(
                    model="fake",
                    content='{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Inspect the README."}',
                    raw={"messages": len(messages)},
                )

        agent = WorkspaceAgent(Path("."), llm_client=FakeToolCallingClient())

        run = agent.run("Use tool calling to read README.md.")

        self.assertIn("Result: read README.md", run.answer)
        self.assertTrue(any(step.title == "Run tool-call graph" for step in run.steps))
        self.assertEqual((run.tool_result.metadata or {}).get("graph_route") if run.tool_result else None, "tool_call_execution")

    def test_agent_tool_loop_runs_through_default_graph_runtime(self) -> None:
        class FakeToolLoopClient:
            def __init__(self) -> None:
                self.calls = 0

            def chat(self, messages):  # noqa: ANN001
                responses = [
                    '{"action":"use_tool","tool_name":"read_file","tool_input":"README.md","reason":"Read the README first."}',
                    '{"action":"answer_directly","tool_name":null,"tool_input":null,"reason":"The README observation is enough."}',
                    "The README was read successfully, so the tool loop has enough evidence to answer.",
                ]
                response = responses[min(self.calls, len(responses) - 1)]
                self.calls += 1
                return LLMResponse(model="fake", content=response, raw={"messages": len(messages)})

        agent = WorkspaceAgent(Path("."), llm_client=FakeToolLoopClient())

        run = agent.run("Use tool loop to read README.md and then answer.")

        self.assertTrue(any(step.title == "Run tool-loop graph" for step in run.steps))
        self.assertEqual(run.tool_loop_result.stop_reason if run.tool_loop_result else "", "model_answered_directly")
        self.assertEqual(run.tool_loop_result.final_answer_source if run.tool_loop_result else "", "llm")

    def test_agent_describes_project_dirs(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("List the main project directories and explain what they are responsible for.")
        self.assertIn("Responsibilities", run.answer)
        self.assertIn("`agent/`", run.answer)

    def test_agent_runs_langgraph_search(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Use LangGraph to search docs for MCP.")

        self.assertEqual(run.route.action, "graph")
        self.assertEqual(run.route.tool_name, "langgraph_workflow")
        self.assertEqual(run.tool_result.tool_name if run.tool_result else None, "langgraph_workflow")
        self.assertIn("Graph route: search_docs", run.answer)
        self.assertIn("Selected tool: search_workspace_docs", run.answer)
        self.assertIn("relevant local context", run.answer)

    def test_agent_runs_langgraph_read_file(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Use LangGraph to read README.md.")

        self.assertIn("Graph route: read_file", run.answer)
        self.assertIn("Selected tool: read_workspace_file", run.answer)
        self.assertIn("[read_file] README.md", run.answer)

    def test_agent_runs_langgraph_no_context_without_network(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Use LangGraph to answer: the and of")

        self.assertIn("Graph route: answer_docs_with_llm", run.answer)
        self.assertIn("Selected tool: answer_workspace_docs_with_llm", run.answer)
        self.assertIn("insufficient", run.answer)

    def test_agent_records_langgraph_trace_step(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Use LangGraph to search docs for MCP.")

        self.assertTrue(any(step.title == "Run graph" for step in run.steps))
        trace_text = agent.format_trace(run)
        self.assertIn("route=search_docs", trace_text)
        self.assertIn("[Runtime Events]", trace_text)

    def test_agent_langgraph_skill_trace_dict_contains_skill_run(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Use LangGraph to execute skill for code review.")

        trace = agent.to_trace_dict(run)

        self.assertEqual(trace["route"]["action"], "graph")
        self.assertEqual(trace["tool_result"]["metadata"]["graph_route"], "skill_execution")
        self.assertEqual(trace["skill_run"]["skill"]["name"], "code_review")
        self.assertEqual(trace["skill_run"]["status"], "completed")
        self.assertIn("Skill status: completed", run.answer)

    def test_agent_langgraph_metadata_contains_recovery_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            agent = WorkspaceAgent(root)

            run = agent.run("Use LangGraph to execute skill for learning explanation.")
            trace = agent.to_trace_dict(run)

            self.assertEqual(trace["skill_run"]["status"], "failed")
            self.assertEqual(trace["tool_result"]["metadata"]["skill_status"], "failed")
            self.assertEqual(trace["tool_result"]["metadata"]["recovery_plan"]["skill_name"], "learning_explanation")
            self.assertTrue(any(event["event_type"] == "recovery" for event in trace["runtime_events"]))
            self.assertIn("Skill recovery plan", run.answer)

    def test_agent_langgraph_metadata_contains_tool_recovery_plan(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            agent = WorkspaceAgent(root)

            run = agent.run("Use LangGraph to read missing.md.")
            trace = agent.to_trace_dict(run)

            metadata = trace["tool_result"]["metadata"]
            self.assertEqual(metadata["graph_route"], "read_file")
            self.assertEqual(metadata["tool_status"], "failed")
            self.assertEqual(metadata["recovery_plan"]["tool_name"], "read_workspace_file")
            self.assertEqual(metadata["recovery_plan"]["failure_type"], "missing_resource")
            self.assertEqual(metadata["recovery_plan"]["source_type"], "tool")
            self.assertTrue(any(event["event_type"] == "recovery" for event in trace["runtime_events"]))
            self.assertIn("Tool recovery plan", run.answer)

    def test_agent_exports_structured_trace(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("List available skills.")

        trace = agent.to_trace_dict(run)

        self.assertEqual(trace["route"]["tool_name"], "list_skills")
        self.assertIn("steps", trace)
        self.assertIn("runtime_events", trace)
        self.assertIn("answer_preview", trace)


if __name__ == "__main__":
    unittest.main()
