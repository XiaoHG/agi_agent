"""Tests for DeepSeek-grounded RAG boundaries."""

from pathlib import Path
import tempfile
import unittest

from agent.llm import LLMResponse
from rag.llm_qa import answer_question_with_llm, build_grounded_rag_prompt
from rag import Document, chunk_document
from rag.retrieval import SearchResult


class StubLLMClient:
    """Small local stub that records messages without making network calls."""

    def __init__(self) -> None:
        self.messages = []

    def chat(self, messages):
        """Return a deterministic response for tests."""

        self.messages = messages
        return LLMResponse(model="test-model", content="Use README.md:1-1 as the source.", raw={})


class GroundedRAGTests(unittest.TestCase):
    """Verify prompt construction and grounded answer boundaries."""

    def test_build_grounded_rag_prompt_includes_sources(self) -> None:
        document = Document(source="README.md", text="agent tools")
        chunk = chunk_document(document, max_lines=1, overlap=0)[0]
        result = SearchResult(chunk=chunk, score=2, matched_terms=("agent", "tools"))

        prompt = build_grounded_rag_prompt("Why do agents need tools?", [result])

        self.assertIn("Question:", prompt)
        self.assertIn("README.md:1-1", prompt)
        self.assertIn("agent tools", prompt)
        self.assertIn("using only the local context", prompt)

    def test_answer_question_with_llm_returns_no_context_without_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")

            answer = answer_question_with_llm(root, "zzzz-not-existing-keyword", llm_client=StubLLMClient())

            self.assertEqual(answer.sources, [])
            self.assertIn("insufficient", answer.answer)

    def test_answer_question_with_llm_preserves_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent tools need context", encoding="utf-8")
            client = StubLLMClient()

            answer = answer_question_with_llm(root, "agent tools", llm_client=client)

            self.assertEqual(answer.sources, ["README.md:1-1"])
            self.assertIn("README.md:1-1", answer.answer)
            self.assertEqual(client.messages[0].role, "system")
            self.assertEqual(client.messages[1].role, "user")

    def test_answer_question_with_llm_uses_vector_index_sources(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("professional rag workflow", encoding="utf-8")
            client = StubLLMClient()

            answer = answer_question_with_llm(root, "professional rag workflow", llm_client=client)

            self.assertEqual(answer.sources, ["README.md:1-1"])
            self.assertIn("README.md:1-1", answer.answer)


if __name__ == "__main__":
    unittest.main()
