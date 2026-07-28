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

    def test_rag_graph_records_route_reason(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = run_rag_graph(root, "Search docs for agent workflow.")

            self.assertIn("route_reason", result)
            self.assertIn("local context", result["route_reason"])


if __name__ == "__main__":
    unittest.main()
