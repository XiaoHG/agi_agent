"""Tests for skills and subagent collaboration."""

from pathlib import Path
import subprocess  # 验证 CLI demo 能真实运行
import sys  # 使用当前 Python 解释器执行模块
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from skills import (
    SkillToolRequest,
    SkillToolResponse,
    build_skill_steps,
    describe_skills,
    discover_project_skills,
    execute_skill,
    get_available_skills,
    select_skill,
)
from subagent import build_collaboration_plan, describe_subagents


class CollaborationTests(unittest.TestCase):
    """Verify skills, subagents, and Agent integration."""

    def test_describe_skills(self) -> None:
        output = describe_skills(Path("."))

        self.assertIn("Available skills", output)
        self.assertIn("research_brief", output)
        self.assertIn("code_review", output)
        self.assertIn("professional-code-review", output)
        self.assertIn("Source: project", output)

    def test_discover_project_skills(self) -> None:
        skills = discover_project_skills(Path("."))

        self.assertEqual(len(skills), 1)
        self.assertEqual(skills[0].name, "professional-code-review")
        self.assertEqual(skills[0].source, "project")
        self.assertTrue((skills[0].path or "").endswith(".codex/skills/professional-code-review/SKILL.md"))

    def test_get_available_skills_merges_builtin_and_project(self) -> None:
        names = {skill.name for skill in get_available_skills(Path("."))}

        self.assertIn("code_review", names)
        self.assertIn("professional-code-review", names)

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
        run = execute_skill("Review this code and add tests.", root=Path("."))

        self.assertEqual(run.skill.name, "code_review")
        self.assertEqual(run.status, "completed")
        self.assertEqual(len(run.steps), len(run.skill.steps))
        self.assertIn("Executed skill 'code_review'", run.final_output)

    def test_build_skill_steps_marks_tool_backed_steps(self) -> None:
        skill = select_skill("Review this code and add tests.", root=Path("."))

        steps = build_skill_steps(skill, "Review this code and add tests.")

        self.assertEqual(steps[0].action, "tool")
        self.assertEqual(steps[0].tool_name, "list_dir")
        self.assertEqual(steps[-1].action, "record")

    def test_execute_skill_uses_tool_runner(self) -> None:
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            return SkillToolResponse(request.tool_name, f"tool output for {request.tool_input}")

        run = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path("."))

        self.assertEqual(run.status, "completed")
        self.assertIn("tool-backed steps: 3", run.final_output)
        self.assertIn("tool output", run.steps[0].observation)

    def test_skill_run_exports_trace_dict(self) -> None:
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            return SkillToolResponse(request.tool_name, f"tool output for {request.tool_input}")

        payload = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path(".")).to_dict()

        self.assertEqual(payload["skill"]["name"], "code_review")
        self.assertEqual(payload["skill"]["source"], "builtin")
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["tool_backed_steps"], 3)
        self.assertEqual(payload["steps"][0]["tool_name"], "list_dir")

    def test_execute_skill_stops_on_tool_error(self) -> None:
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            return SkillToolResponse(request.tool_name, "tool failed", is_error=True)

        run = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path("."))

        self.assertEqual(run.status, "failed")
        self.assertEqual(len(run.steps), 1)
        self.assertEqual(run.steps[0].status, "failed")
        self.assertIn("failed steps: 1", run.final_output)

    def test_select_project_skill_by_name(self) -> None:
        skill = select_skill("Execute skill professional-code-review.", root=Path("."))

        self.assertEqual(skill.name, "professional-code-review")
        self.assertEqual(skill.source, "project")

    def test_execute_project_skill_returns_structured_run(self) -> None:
        run = execute_skill(
            "Review the current changes before commit.",
            root=Path("."),
            skill_name="professional-code-review",
        )

        self.assertEqual(run.skill.name, "professional-code-review")
        self.assertEqual(run.skill.source, "project")
        self.assertEqual(run.status, "completed")
        self.assertGreaterEqual(len(run.steps), 4)
        self.assertIn("Expected output format:", run.final_output)

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
        self.assertIn("professional-code-review", run.answer)

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
        self.assertIn("tool-backed steps", run.answer)
        self.assertIn("[list_dir]", run.answer)

    def test_agent_trace_dict_contains_skill_run(self) -> None:
        agent = WorkspaceAgent(Path("."))

        trace = agent.to_trace_dict(agent.run("Execute skill for code review."))

        self.assertIsNotNone(trace["skill_run"])
        self.assertEqual(trace["skill_run"]["skill"]["name"], "code_review")
        self.assertEqual(trace["skill_run"]["skill"]["source"], "builtin")
        self.assertEqual(trace["skill_run"]["status"], "completed")
        self.assertEqual(trace["skill_run"]["tool_backed_steps"], 3)

    def test_agent_executes_project_skill(self) -> None:
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute skill professional-code-review.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.tool_name, "execute_skill")
        self.assertIn("Skill run: professional-code-review", run.answer)
        self.assertEqual(trace["skill_run"]["skill"]["source"], "project")

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

    def test_collaboration_demo_executes_tool_backed_skill(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Review this code and add tests.",
                "--execute-skill",
                "--tool-backed",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Skill run: code_review", result.stdout)
        self.assertIn("tool-backed steps", result.stdout)
        self.assertIn("[list_dir]", result.stdout)
        self.assertNotIn("Planned tool: list_dir", result.stdout)

    def test_collaboration_demo_lists_project_skills(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "cli.collaboration_demo", "--list-skills"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("professional-code-review", result.stdout)
        self.assertIn("Source: project", result.stdout)

    def test_collaboration_demo_executes_project_skill(self) -> None:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Review current changes.",
                "--execute-skill",
                "--skill",
                "professional-code-review",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Skill run: professional-code-review", result.stdout)
        self.assertIn("Status: completed", result.stdout)


if __name__ == "__main__":
    unittest.main()
