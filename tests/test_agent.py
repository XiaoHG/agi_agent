"""Tests for the minimal workspace agent."""

from pathlib import Path
import tempfile
import unittest

from agent import WorkspaceAgent, list_dir, read_file, route_intent


class WorkspaceAgentTests(unittest.TestCase):
    """Verify routing, tools, and user-facing behaviors."""

    def test_route_to_read_file(self) -> None:
        route = route_intent("请读取 README.md，并总结这个项目的学习目标。")
        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "read_file")
        self.assertEqual(route.tool_input, "README.md")

    def test_route_to_list_dir(self) -> None:
        route = route_intent("请查看当前项目有哪些主要目录，并说明它们分别负责什么。")
        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_dir")

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
        run = agent.run("请解释 Agent 和普通聊天机器人的区别。")
        self.assertIn("Agent 和普通聊天机器人最大的区别", run.answer)
        self.assertEqual(run.route.action, "direct_answer")

    def test_agent_handles_missing_file(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("请读取 not-exist.md。")
        self.assertIn("工具调用失败", run.answer)
        self.assertIn("文件不存在", run.tool_error or "")

    def test_agent_summarizes_readme_learning_goals(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("请读取 README.md，并总结这个项目的学习目标。")
        self.assertIn("项目学习目标包括", run.answer)
        self.assertIn("理解 Agent", run.answer)

    def test_agent_describes_project_dirs(self) -> None:
        agent = WorkspaceAgent(Path("."))
        run = agent.run("请查看当前项目有哪些主要目录，并说明它们分别负责什么。")
        self.assertIn("核心职责", run.answer)
        self.assertIn("`agent/`", run.answer)


if __name__ == "__main__":
    unittest.main()

