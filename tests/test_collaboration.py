"""Tests for skills and subagent collaboration."""

from pathlib import Path
import subprocess  # 验证 CLI demo 能真实运行
import sys  # 使用当前 Python 解释器执行模块
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from skills import describe_skills, execute_skill, select_skill
from subagent import build_collaboration_plan, describe_subagents


class CollaborationTests(unittest.TestCase):
    """Verify skills, subagents, and Agent integration."""

    def test_describe_skills(self) -> None:
        output = describe_skills()

        self.assertIn("Available skills", output)
        self.assertIn("research_brief", output)
        self.assertIn("code_review", output)

    def test_select_code_review_skill(self) -> None:
        skill = select_skill("Review this code and add tests.")

        self.assertEqual(skill.name, "code_review")

    def test_select_explain_skill(self) -> None:
        skill = select_skill("Explain how workflow works.")

        self.assertEqual(skill.name, "learning_explanation")

    def test_research_skill(self) -> None:
        skill = select_skill("Research MCP adoption patterns.")

        self.assertEqual(skill.name, "research_brief")

    def test_execute_skill_returns_structured_run(self) -> None:
        run = execute_skill("Review this code and add tests.")

        self.assertEqual(run.skill.name, "code_review")
        self.assertEqual(run.status, "completed")
        self.assertEqual(len(run.steps), len(run.skill.steps))
        self.assertIn("Executed skill 'code_review'", run.final_output)

    def test_describe_subagents(self) -> None:
        output = describe_subagents()

        self.assertIn("teacher_agent", output)
        self.assertIn("coding_agent", output)

    def test_build_collaboration_plan_for_code_task(self) -> None:
        plan = build_collaboration_plan("Implement a bug fix and test it.")

        self.assertIn("coding_agent", plan.to_text())
        self.assertIn("Teacher Agent explains", plan.to_text())

    def test_build_collaboration_plan_for_teacher_task(self) -> None:
        plan = build_collaboration_plan("Explain RAG architecture.")

        self.assertIn("teacher_agent", plan.to_text())
        self.assertNotIn("coding_agent", plan.to_text())

    def test_route_to_list_skills(self) -> None:
        route = route_intent("List available skills.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_skills")

    def test_route_to_execute_skill(self) -> None:
        route = route_intent("Execute skill for code review.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "execute_skill")

    def test_route_to_plan_subagents(self) -> None:
        route = route_intent("Plan subagent collaboration for a code review.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "plan_subagents")

    def test_agent_lists_skills(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("List available skills.")

        self.assertEqual(run.route.tool_name, "list_skills")
        self.assertIn("Available skills", run.answer)

    def test_agent_plans_subagent_collaboration(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Plan subagent collaboration for a code review.")

        self.assertEqual(run.route.tool_name, "plan_subagents")
        self.assertIn("Collaboration objective", run.answer)

    def test_agent_executes_skill(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute skill for code review.")

        self.assertEqual(run.route.tool_name, "execute_skill")
        self.assertIn("Skill run: code_review", run.answer)
        self.assertIn("Executed steps", run.answer)

    def test_collaboration_demo_cli(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cli.collaboration_demo", "--task", "Review this code and add tests."],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Skill: code_review", result.stdout)
        self.assertIn("coding_agent", result.stdout)

    def test_collaboration_demo_executes_skill(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Review this code and add tests.",
                "--execute-skill",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Skill run: code_review", result.stdout)
        self.assertIn("Status: completed", result.stdout)


if __name__ == "__main__":
    unittest.main()
