"""Tests for the local RAG retrieval layer."""

from pathlib import Path
import tempfile  # 使用临时工作区，避免依赖真实项目文件
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, answer_docs_with_llm, route_intent, search_docs, search_vector_docs
from cli import rag_index_demo
from rag import (
    CitationValidationResult,
    Document,
    answer_question,
    build_vector_index,
    build_document_fingerprints,
    chunk_document,
    load_vector_index,
    load_text_documents,
    plan_vector_index_update,
    retrieve,
    save_vector_index,
    search_vector_index,
    update_vector_index,
    validate_answer_citations,
)


class LocalRAGTests(unittest.TestCase):
    """Verify local document loading, chunking, retrieval, and agent routing."""

    def test_load_text_documents(self) -> None:
        """Verify that load text documents."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "docs").mkdir()
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            (root / "docs" / "note.md").write_text("rag retrieval", encoding="utf-8")

            documents = load_text_documents(root, paths=("README.md", "docs"))
            sources = {document.source for document in documents}

            self.assertEqual(sources, {"README.md", "docs/note.md"})

    def test_chunk_document(self) -> None:
        """Verify that chunk document."""
        document = Document(source="demo.md", text="one\ntwo\nthree\nfour")

        chunks = chunk_document(document, max_lines=2, overlap=1)

        self.assertEqual(len(chunks), 3)
        self.assertEqual(chunks[0].source_label(), "demo.md:1-2")
        self.assertEqual(chunks[1].text, "two\nthree")

    def test_retrieve_returns_ranked_context(self) -> None:
        """Verify that retrieve returns ranked context."""
        document = Document(source="demo.md", text="agent workflow\nrag retrieval\nagent state")
        chunks = chunk_document(document, max_lines=1, overlap=0)

        results = retrieve(chunks, "agent workflow", top_k=2)

        self.assertEqual(results[0].chunk.text, "agent workflow")
        self.assertGreaterEqual(results[0].score, results[1].score)

    def test_vector_index_saves_chunk_metadata(self) -> None:
        """Verify that vector index saves chunk metadata."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\nrag retrieval", encoding="utf-8")

            index = build_vector_index(root, paths=("README.md",), max_lines=1, overlap=0)

            self.assertEqual(index.records[0].metadata["citation"], "README.md:1-1")
            self.assertEqual(index.dimensions, 64)
            self.assertEqual(index.embedding_backend["name"], "local_hash_embedding")
            self.assertEqual(index.index_backend["name"], "json_vector_index")
            self.assertIn("README.md", index.document_fingerprints)

    def test_vector_index_round_trips_json(self) -> None:
        """Verify that vector index round trips json."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            index_path = root / "data" / "rag-index.json"

            saved_path = save_vector_index(build_vector_index(root, paths=("README.md",)), index_path)
            loaded = load_vector_index(saved_path)

            self.assertEqual(len(loaded.records), 1)
            self.assertEqual(loaded.records[0].chunk.source_label(), "README.md:1-1")

    def test_search_vector_index_returns_citations(self) -> None:
        """Verify that search vector index returns citations."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\nrag retrieval", encoding="utf-8")
            index = build_vector_index(root, paths=("README.md",), max_lines=1, overlap=0)

            results = search_vector_index(index, "agent workflow", top_k=1)

            self.assertEqual(results[0].citation(), "README.md:1-1")

    def test_build_document_fingerprints_stays_stable(self) -> None:
        """Verify that build document fingerprints stays stable."""
        documents = [Document(source="README.md", text="agent workflow")]

        left = build_document_fingerprints(documents)
        right = build_document_fingerprints(documents)

        self.assertEqual(left, right)
        self.assertIn("README.md", left)

    def test_plan_vector_index_update_marks_changed_sources(self) -> None:
        """Verify that plan vector index update marks changed sources."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            current = build_vector_index(root, paths=("README.md",), max_lines=1, overlap=0)

            (root / "README.md").write_text("agent workflow updated", encoding="utf-8")

            plan = plan_vector_index_update(root, current, paths=("README.md",))

            self.assertEqual(plan.changed_sources, ("README.md",))
            self.assertEqual(plan.added_sources, ())
            self.assertEqual(plan.removed_sources, ())

    def test_update_vector_index_rebuilds_only_changed_sources(self) -> None:
        """Verify that update vector index rebuilds only changed sources."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            (root / "docs").mkdir()
            (root / "docs" / "note.md").write_text("rag retrieval", encoding="utf-8")
            current = build_vector_index(root, paths=("README.md", "docs"), max_lines=1, overlap=0)
            old_note_records = [record for record in current.records if record.chunk.source == "docs/note.md"]

            (root / "README.md").write_text("agent workflow updated", encoding="utf-8")

            updated, plan = update_vector_index(root, current, paths=("README.md", "docs"), max_lines=1, overlap=0)

            self.assertEqual(plan.changed_sources, ("README.md",))
            self.assertEqual(plan.unchanged_sources, ("docs/note.md",))
            note_records = [record for record in updated.records if record.chunk.source == "docs/note.md"]
            self.assertEqual(
                [record.metadata["document_fingerprint"] for record in note_records],
                [record.metadata["document_fingerprint"] for record in old_note_records],
            )
            self.assertTrue(any("updated" in record.chunk.text for record in updated.records if record.chunk.source == "README.md"))

    def test_search_docs_tool(self) -> None:
        """Verify that search docs tool."""
        result = search_docs(Path("."), "search docs workflow")

        self.assertEqual(result.tool_name, "search_docs")
        self.assertIn("Source 1", result.output)
        self.assertIn("workflow", result.output.lower())

    def test_search_vector_docs_tool(self) -> None:
        """Verify that search vector docs tool."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("professional rag workflow", encoding="utf-8")

            result = search_vector_docs(root, "professional RAG workflow")

            self.assertEqual(result.tool_name, "search_vector_docs")
            self.assertIn("Citation 1", result.output)
            self.assertIn("Vector score", result.output)
            self.assertEqual(result.metadata["backend"]["name"], "local_hash_embedding")

    def test_route_to_search_docs(self) -> None:
        """Verify that route to search docs."""
        route = route_intent("Search docs for workflow.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "search_docs")

    def test_route_to_search_vector_docs(self) -> None:
        """Verify that route to search vector docs."""
        route = route_intent("Use professional RAG to search docs for workflow.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "search_vector_docs")

    def test_route_to_answer_docs_with_llm(self) -> None:
        """Verify that route to answer docs with llm."""
        route = route_intent("Answer with local docs and DeepSeek RAG: What does workflow mean?")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "answer_docs_with_llm")
        self.assertEqual(route.tool_input, "What does workflow mean?")

    def test_agent_searches_local_docs(self) -> None:
        """Verify that agent searches local docs."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Search docs for workflow.")

        self.assertEqual(run.route.tool_name, "search_docs")
        self.assertIn("relevant local context", run.answer)

    def test_agent_searches_vector_docs(self) -> None:
        """Verify that agent searches vector docs."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("professional rag workflow", encoding="utf-8")
            agent = WorkspaceAgent(root)

            run = agent.run("Use professional RAG to search docs for workflow.")

            self.assertEqual(run.route.tool_name, "search_vector_docs")
            self.assertIn("vector context", run.answer)

    def test_rag_index_demo_rebuilds_index(self) -> None:
        """Verify that rag index demo rebuilds index."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            exit_code = rag_index_demo.main(["--root", str(root), "--output", "data/rag-index.json"])

            self.assertEqual(exit_code, 0)
            self.assertTrue((root / "data" / "rag-index.json").exists())

    def test_answer_docs_with_llm_tool_handles_no_context(self) -> None:
        """Verify that answer docs with llm tool handles no context."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            result = answer_docs_with_llm(root, "qa-no-context-token-928374")

            self.assertEqual(result.tool_name, "answer_docs_with_llm")
            self.assertIn("insufficient", result.output)
            self.assertTrue(result.metadata["citation_validation"]["valid"])

    def test_agent_answers_docs_with_llm_without_context(self) -> None:
        """Verify that agent answers docs with llm without context."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            agent = WorkspaceAgent(root)

            run = agent.run("Answer with local docs and DeepSeek RAG: qa-no-context-token-928374")

            self.assertEqual(run.route.tool_name, "answer_docs_with_llm")
            self.assertIn("insufficient", run.answer)

    def test_agent_searches_mcp(self) -> None:
        """Verify that agent searches mcp."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Search docs for MCP.")

        self.assertEqual(run.route.tool_name, "search_docs")
        self.assertIn("relevant local context", run.answer)

    def test_rag_returns_empty_result_for_unknown_keyword(self) -> None:
        """Verify that rag returns empty result for unknown keyword."""
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            answer = answer_question(root, "zzzz-not-existing-keyword")

            self.assertEqual(answer.results, [])
            self.assertIn("no local context", answer.to_text())

    def test_validate_answer_citations_accepts_supported_sources(self) -> None:
        """Verify that validate answer citations accepts supported sources."""
        result = validate_answer_citations(
            "Use README.md:1-1 for the answer.",
            ["README.md:1-1"],
        )

        self.assertTrue(result.valid)
        self.assertEqual(result.cited_sources, ("README.md:1-1",))

    def test_validate_answer_citations_rejects_unsupported_sources(self) -> None:
        """Verify that validate answer citations rejects unsupported sources."""
        result = validate_answer_citations(
            "Use README.md:1-1 and docs/plan.md:2-4 for the answer.",
            ["README.md:1-1"],
        )

        self.assertFalse(result.valid)
        self.assertEqual(result.unsupported_citations, ("docs/plan.md:2-4",))


if __name__ == "__main__":
    unittest.main()
