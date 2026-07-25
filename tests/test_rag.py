"""Tests for the local RAG retrieval layer."""

from pathlib import Path
import tempfile  # 使用临时工作区，避免依赖真实项目文件
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent, search_docs
from rag import Document, answer_question, chunk_document, load_text_documents, retrieve


class LocalRAGTests(unittest.TestCase):
    """Verify local document loading, chunking, retrieval, and agent routing."""

    def test_load_text_documents(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            (root / "docs" / "note.md").write_text("rag retrieval", encoding="utf-8")

            documents = load_text_documents(root, paths=("README.md", "docs"))
            sources = {document.source for document in documents}

            self.assertEqual(sources, {"README.md", "docs/note.md"})

    def test_chunk_document(self) -> None:
        document = Document(source="demo.md", text="one\ntwo\nthree\nfour")

        chunks = chunk_document(document, max_lines=2, overlap=1)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].source_label(), "demo.md:1-2")
        self.assertEqual(chunks[1].text, "two\nthree")

    def test_retrieve_returns_ranked_context(self) -> None:
        document = Document(source="demo.md", text="agent workflow\nrag retrieval\nagent state")
        chunks = chunk_document(document, max_lines=1, overlap=0)

        results = retrieve(chunks, "agent workflow", top_k=2)

        self.assertEqual(results[0].chunk.text, "agent workflow")
        self.assertGreaterEqual(results[0].score, results[1].score)

    def test_search_docs_tool(self) -> None:
        result = search_docs(Path("."), "search docs workflow")

        self.assertEqual(result.tool_name, "search_docs")
        self.assertIn("Source 1", result.output)
        self.assertIn("workflow", result.output.lower())

    def test_route_to_search_docs(self) -> None:
        route = route_intent("Search docs for workflow.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "search_docs")

    def test_agent_searches_local_docs(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Search docs for workflow.")

        self.assertEqual(run.route.tool_name, "search_docs")
        self.assertIn("relevant local context", run.answer)

    def test_agent_searches_mcp(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Search docs for MCP.")

        self.assertEqual(run.route.tool_name, "search_docs")
        self.assertIn("relevant local context", run.answer)

    def test_rag_returns_empty_result_for_unknown_keyword(self) -> None:
        answer = answer_question(Path("."), "zzzz-not-existing-keyword")

        self.assertEqual(answer.results, [])
        self.assertIn("no local context", answer.to_text())


if __name__ == "__main__":
    unittest.main()
