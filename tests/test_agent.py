"""Tests for the minimal workspace agent."""

from pathlib import Path
import tempfile  # 临时文件夹，测试完自动删，不污染环境
import unittest  # Python 官方测试框架
import re

from agent import WorkspaceAgent, list_dir, read_file, count_lines, route_intent


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
        self.assertEqual(route.tool_input, re.search(r'([\w-]+\.\w+)', text).group(1) if re.search(r'([\w-]+\.\w+)', text) else ".")

    def test_route_to_workflow(self) -> None:
        text = "Read README.md and then count lines."
        route = route_intent(text)
        self.assertEqual(route.action, "workflow")

    def test_workflow_run(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Read README.md and then count lines.")
        self.assertIn("workflow completed", run.answer)
        self.assertIn("count_lines", run.answer)

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
        agent = WorkspaceAgent(Path("."))
        run = agent.run("Explain the difference between an agent and a chatbot.")
        self.assertIn("main difference", run.answer)
        self.assertEqual(run.route.action, "direct_answer")

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

    def test_agent_describes_project_dirs(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("List the main project directories and explain what they are responsible for.")
        self.assertIn("Responsibilities", run.answer)
        self.assertIn("`agent/`", run.answer)


if __name__ == "__main__":
    unittest.main()
