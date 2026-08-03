"""Tests for the LangGraph RAG workflow."""

from pathlib import Path
import tempfile
import unittest

from integrations.langgraph_workflow import build_rag_graph, run_rag_graph


class LangGraphWorkflowTests(unittest.TestCase):
    """Verify the minimal LangGraph workflow runs through expected graph nodes."""

    def test_build_rag_graph_returns_invokable_graph(self) -> None:
        graph = build_rag_graph(Path("."))

        self.assertTrue(hasattr(graph, "invoke"))

    def test_rag_graph_handles_no_context_without_network(self) -> None:
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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Search docs for agent workflow.")

            self.assertEqual(result["route"], "search_docs")
            self.assertEqual(result["selected_tool"], "search_workspace_docs")
            self.assertIn("relevant local context", result["answer"])

    def test_rag_graph_routes_to_read_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Read README.md.")

            self.assertEqual(result["route"], "read_file")
            self.assertEqual(result["selected_tool"], "read_workspace_file")
            self.assertIn("[read_file] README.md", result["answer"])

    def test_rag_graph_recovers_failed_tool_call(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)

            result = run_rag_graph(root, "Read missing.md.")

            self.assertEqual(result["route"], "read_file")
            self.assertEqual(result["tool_status"], "failed")
            self.assertEqual(result["steps"], ["route", "call_tool", "recover_tool_failure", "finalize"])
            self.assertEqual(result["recovery_plan"]["tool_name"], "read_workspace_file")
            self.assertEqual(result["recovery_plan"]["failure_type"], "missing_resource")
            self.assertIn("Tool recovery plan", result["answer"])

    def test_rag_graph_tool_status_controls_next_edge(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Read README.md.")

            self.assertEqual(result["tool_status"], "completed")
            self.assertEqual(result["steps"], ["route", "call_tool", "finalize"])
            self.assertNotIn("recovery_plan", result)

    def test_rag_graph_routes_to_skill_execution(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Execute skill for code review.")

            self.assertEqual(result["route"], "skill_execution")
            self.assertEqual(result["selected_tool"], "execute_workspace_skill")
            self.assertEqual(result["skill_status"], "completed")
            self.assertEqual(result["steps"], ["route", "call_skill", "finalize"])
            self.assertIn("Skill run: code_review", result["answer"])

    def test_rag_graph_keeps_skill_run_trace(self) -> None:
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
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Use skill for code review.")

            self.assertEqual(result["skill_status"], "completed")
            self.assertEqual(result["steps"][-1], "finalize")
            self.assertNotIn("error", result)

    def test_rag_graph_recovers_failed_skill_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Use skill for learning explanation.")

            self.assertEqual(result["skill_status"], "failed")
            self.assertEqual(result["steps"], ["route", "call_skill", "recover_skill_failure", "finalize"])
            self.assertEqual(result["recovery_plan"]["skill_name"], "learning_explanation")
            self.assertIn("docs/current-learning-state.md", result["recovery_plan"]["reason"])
            self.assertIn("Skill recovery plan", result["answer"])

    def test_rag_graph_records_route_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Search docs for agent workflow.")

            self.assertIn("route_reason", result)
            self.assertIn("local context", result["route_reason"])


if __name__ == "__main__":
    unittest.main()
