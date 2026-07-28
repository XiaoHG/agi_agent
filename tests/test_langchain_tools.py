"""Tests for LangChain tool adapters."""

from pathlib import Path
import tempfile
import unittest

from langchain_core.tools import StructuredTool

from integrations import build_langchain_tools


class LangChainToolAdapterTests(unittest.TestCase):
    """Verify local tools are exposed as real LangChain StructuredTool objects."""

    def test_build_langchain_tools_returns_structured_tools(self) -> None:
        tools = build_langchain_tools(Path("."))

        self.assertTrue(tools)
        self.assertTrue(all(isinstance(tool, StructuredTool) for tool in tools))

    def test_tool_specs_include_expected_tools(self) -> None:
        tools = build_langchain_tools(Path("."))
        names = {tool.name for tool in tools}

        self.assertIn("read_workspace_file", names)
        self.assertIn("search_workspace_docs", names)
        self.assertIn("answer_workspace_docs_with_llm", names)
        self.assertIn("plan_workspace_subagents", names)

    def test_read_file_tool_invokes_core_tool(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent tools", encoding="utf-8")
            tools = {tool.name: tool for tool in build_langchain_tools(root)}

            output = tools["read_workspace_file"].invoke({"path": "README.md"})

            self.assertIn("[read_file] README.md", output)
            self.assertIn("agent tools", output)

    def test_llm_rag_tool_marks_network_dependency(self) -> None:
        tools = {tool.name: tool for tool in build_langchain_tools(Path("."))}

        metadata = tools["answer_workspace_docs_with_llm"].metadata

        self.assertEqual(metadata["requires_network"], True)
        self.assertEqual(metadata["requires_api_key"], "DEEPSEEK_API_KEY")

    def test_no_argument_tool_invokes_without_arguments(self) -> None:
        tools = {tool.name: tool for tool in build_langchain_tools(Path("."))}

        output = tools["list_workspace_skills"].invoke({})

        self.assertIn("Available skills", output)


if __name__ == "__main__":
    unittest.main()
