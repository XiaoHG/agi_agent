"""Tests for skills and subagent collaboration."""

from pathlib import Path
import subprocess  # 验证 CLI demo 能真实运行
import sys  # 使用当前 Python 解释器执行模块
import unittest  # Python 官方测试框架

from agent import WorkspaceAgent, route_intent
from skills import (
    SkillGovernancePolicy,
    SkillToolRequest,
    SkillToolResponse,
    SkillRuntimePolicy,
    build_skill_steps,
    describe_skills,
    build_default_skill_governance_policy,
    discover_project_skills,
    execute_skill,
    get_available_skills,
    select_skill,
    validate_skill_governance,
)
from subagent import build_collaboration_plan, build_subagent_task_contract, describe_subagents, execute_collaboration_plan


class CollaborationTests(unittest.TestCase):
    """Verify skills, subagents, and Agent integration."""

    def test_describe_skills(self) -> None:
        """Verify that describe skills."""
        output = describe_skills(Path("."))

        self.assertIn("Available skills", output)
        self.assertIn("Governance protocol: v2", output)
        self.assertIn("research_brief", output)
        self.assertIn("code_review", output)
        self.assertIn("professional-code-review", output)
        self.assertIn("Version: v1", output)
        self.assertIn("Source: project", output)
        self.assertIn("Governance validation: valid", output)

    def test_discover_project_skills(self) -> None:
        """Verify that discover project skills."""
        skills = discover_project_skills(Path("."))

        self.assertGreaterEqual(len(skills), 2)
        names = {skill.name for skill in skills}
        self.assertIn("professional-code-review", names)
        self.assertIn("publish-book-workflow", names)
        self.assertIn("publish-chapter-full-cycle", names)
        self.assertTrue(any(skill.source == "project" for skill in skills))
        self.assertTrue(any((skill.path or "").endswith(".codex/skills/professional-code-review/SKILL.md") for skill in skills))

    def test_get_available_skills_merges_builtin_and_project(self) -> None:
        """Verify that get available skills merges builtin and project."""
        names = {skill.name for skill in get_available_skills(Path("."))}

        self.assertIn("code_review", names)
        self.assertIn("professional-code-review", names)

    def test_select_code_review_skill(self) -> None:
        """Verify that select code review skill."""
        skill = select_skill("Review this code and add tests.")

        self.assertEqual(skill.name, "code_review")

    def test_select_explain_skill(self) -> None:
        """Verify that select explain skill."""
        skill = select_skill("Explain how workflow works.")

        self.assertEqual(skill.name, "learning_explanation")

    def test_research_skill(self) -> None:
        """Verify that research skill."""
        skill = select_skill("Research MCP adoption patterns.")

        self.assertEqual(skill.name, "research_brief")

    def test_execute_skill_returns_structured_run(self) -> None:
        """Verify that execute skill returns structured run."""
        run = execute_skill("Review this code and add tests.", root=Path("."))

        self.assertEqual(run.skill.name, "code_review")
        self.assertEqual(run.status, "completed")
        self.assertTrue(run.governance_validation.valid if run.governance_validation else False)
        self.assertEqual(run.governance_policy.protocol_version, "v2")
        self.assertEqual(run.governance_audit[0]["stage"], "registry")
        self.assertEqual(len(run.steps), len(run.skill.steps))
        self.assertIn("Executed skill 'code_review'", run.final_output)

    def test_build_skill_steps_marks_tool_backed_steps(self) -> None:
        """Verify that build skill steps marks tool backed steps."""
        skill = select_skill("Review this code and add tests.", root=Path("."))

        steps = build_skill_steps(skill, "Review this code and add tests.")

        self.assertEqual(steps[0].action, "tool")
        self.assertEqual(steps[0].tool_name, "list_dir")
        self.assertEqual(steps[-1].action, "record")

    def test_execute_skill_uses_tool_runner(self) -> None:
        """Verify that execute skill uses tool runner."""
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            """Execute one requested tool call and normalize the result for the caller."""
            return SkillToolResponse(request.tool_name, f"tool output for {request.tool_input}")

        run = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path("."))

        self.assertEqual(run.status, "completed")
        self.assertIn("tool-backed steps: 3", run.final_output)
        self.assertIn("tool output", run.steps[0].observation)

    def test_skill_run_exports_trace_dict(self) -> None:
        """Verify that skill run exports trace dict."""
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            """Execute one requested tool call and normalize the result for the caller."""
            return SkillToolResponse(request.tool_name, f"tool output for {request.tool_input}")

        payload = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path(".")).to_dict()

        self.assertEqual(payload["skill"]["name"], "code_review")
        self.assertEqual(payload["skill"]["source"], "builtin")
        self.assertEqual(payload["skill"]["declared_tools"], ["list_dir", "search_docs"])
        self.assertEqual(payload["status"], "completed")
        self.assertEqual(payload["governance_policy"]["protocol_version"], "v2")
        self.assertTrue(payload["governance_validation"]["valid"])
        self.assertEqual(payload["governance_audit"][1]["stage"], "validation")
        self.assertEqual(payload["tool_backed_steps"], 3)
        self.assertEqual(payload["steps"][0]["tool_name"], "list_dir")

    def test_validate_skill_governance_accepts_builtin_declared_tools(self) -> None:
        """Verify that validate skill governance accepts builtin declared tools."""
        skill = select_skill("Review this code and add tests.", root=Path("."))

        validation = validate_skill_governance(
            skill,
            executable_tools=("list_dir", "search_docs"),
            policy=build_default_skill_governance_policy(),
        )

        self.assertTrue(validation.valid)
        self.assertEqual(validation.declared_tools, ("list_dir", "search_docs"))
        self.assertEqual(validation.executable_tools, ("list_dir", "search_docs"))

    def test_validate_skill_governance_rejects_undeclared_tools(self) -> None:
        """Verify that validate skill governance rejects undeclared tools."""
        skill = select_skill("Research MCP adoption patterns.", root=Path("."))

        validation = validate_skill_governance(
            skill,
            executable_tools=("search_docs", "read_file"),
            policy=SkillGovernancePolicy(),
        )

        self.assertFalse(validation.valid)
        self.assertEqual(validation.undeclared_tools, ("read_file",))
        self.assertIn("undeclared tool", validation.reason)

    def test_execute_skill_stops_on_tool_error(self) -> None:
        """Verify that execute skill stops on tool error."""
        def runner(request: SkillToolRequest) -> SkillToolResponse:
            """Execute one requested tool call and normalize the result for the caller."""
            return SkillToolResponse(request.tool_name, "tool failed", is_error=True)

        run = execute_skill("Review this code and add tests.", tool_runner=runner, root=Path("."))

        self.assertEqual(run.status, "failed")
        self.assertEqual(len(run.steps), 1)
        self.assertEqual(run.steps[0].status, "failed")
        self.assertIn("failed steps: 1", run.final_output)

    def test_select_project_skill_by_name(self) -> None:
        """Verify that select project skill by name."""
        skill = select_skill("Execute skill professional-code-review.", root=Path("."))

        self.assertEqual(skill.name, "professional-code-review")
        self.assertEqual(skill.source, "project")

    def test_execute_project_skill_returns_structured_run(self) -> None:
        """Verify that execute project skill returns structured run."""
        run = execute_skill(
            "Review the current changes before commit.",
            root=Path("."),
            skill_name="professional-code-review",
        )

        self.assertEqual(run.skill.name, "professional-code-review")
        self.assertEqual(run.skill.source, "project")
        self.assertEqual(run.skill.version, "v1")
        self.assertEqual(run.status, "completed")
        self.assertGreaterEqual(len(run.steps), 4)
        self.assertIn("Expected output format:", run.final_output)

    def test_execute_skill_blocks_project_skill_with_policy(self) -> None:
        """Verify that execute skill blocks project skill with policy."""
        policy = SkillRuntimePolicy(policy_name="builtin-only", allow_builtin=True, allow_project=False)

        run = execute_skill(
            "Review the current changes before commit.",
            root=Path("."),
            skill_name="professional-code-review",
            policy=policy,
        )

        self.assertEqual(run.status, "blocked")
        self.assertEqual(run.skill.name, "professional-code-review")
        self.assertFalse(run.policy_decision.allowed if run.policy_decision else True)
        self.assertIn("Blocked skill", run.final_output)
        self.assertEqual(len(run.steps), 0)

    def test_describe_subagents(self) -> None:
        """Verify that describe subagents."""
        output = describe_subagents()

        self.assertIn("teacher_agent", output)
        self.assertIn("coding_agent", output)
        self.assertIn("Input boundary", output)
        self.assertIn("Output boundary", output)

    def test_build_subagent_task_contract_exports_boundaries(self) -> None:
        """Verify that build subagent task contract exports boundaries."""
        role = next(role for role in build_collaboration_plan("Explain RAG architecture.").assigned_roles if role.name == "teacher_agent")
        contract = build_subagent_task_contract(role, "Explain RAG architecture.")

        data = contract.to_dict()

        self.assertEqual(data["role_name"], "teacher_agent")
        self.assertIn("Clarify the request", data["objective"])
        self.assertIn("learning checkpoint", contract.to_text())

    def test_build_collaboration_plan_for_code_task(self) -> None:
        """Verify that build collaboration plan for code task."""
        plan = build_collaboration_plan("Implement a bug fix and test it.")

        self.assertIn("coding_agent", plan.to_text())
        self.assertIn("Teacher Agent defines the objective", plan.to_text())
        self.assertIn("Coding Agent implements", plan.to_text())
        self.assertIn("Delegations:", plan.to_text())
        self.assertEqual(len(plan.to_dict()["delegations"]), 2)

    def test_execute_collaboration_plan_returns_handoffs_and_returns(self) -> None:
        """Verify that execute collaboration plan returns handoffs and returns."""
        plan = execute_collaboration_plan("Implement a bug fix and test it.")

        self.assertEqual(plan.status, "completed")
        self.assertEqual(len(plan.handoffs), 1)
        self.assertEqual(len(plan.executions), 2)
        self.assertEqual(len(plan.returns), 2)
        self.assertIsNotNone(plan.runtime_session)
        assert plan.runtime_session is not None
        self.assertEqual(plan.runtime_session.status, "completed")
        self.assertEqual(plan.runtime_session.parent_role, "parent_agent")
        self.assertEqual(plan.runtime_session.child_roles, ("teacher_agent", "coding_agent"))
        self.assertEqual(plan.runtime_session.context_boundary.active_role, "parent_agent")
        self.assertGreaterEqual(len(plan.runtime_session.messages), 4)
        self.assertGreaterEqual(len(plan.runtime_session.transitions), 5)
        self.assertEqual(plan.runtime_session.execution_mode, "deterministic-async-delegation")
        self.assertEqual(len(plan.runtime_session.queue_items), 2)
        self.assertEqual(len(plan.runtime_session.inbox_entries), 2)
        self.assertEqual(len(plan.runtime_session.outbox_entries), 2)
        self.assertEqual(len(plan.runtime_session.claim_records), 2)
        self.assertEqual(plan.handoffs[0].from_role, "teacher_agent")
        self.assertEqual(plan.handoffs[0].to_role, "coding_agent")
        self.assertIn("Runtime session:", plan.to_text())
        self.assertIn("Returns:", plan.to_text())

    def test_execute_collaboration_plan_can_fail_and_keep_recovery_handoff(self) -> None:
        """Verify that execute collaboration plan can fail and keep recovery handoff."""
        plan = execute_collaboration_plan("Implement an underspecified ambiguous code change.")

        self.assertEqual(plan.status, "failed")
        self.assertEqual(plan.executions[-1].status, "failed")
        self.assertIsNotNone(plan.runtime_session)
        assert plan.runtime_session is not None
        self.assertEqual(plan.runtime_session.status, "failed")
        self.assertEqual(plan.runtime_session.active_role, "coding_agent")
        self.assertEqual(plan.runtime_session.transitions[-1].to_state, "failed")
        self.assertIn("teacher_agent", plan.recovery_handoff)

    def test_execute_collaboration_plan_can_block_inside_agent_inbox(self) -> None:
        """Verify that execute collaboration plan can block and keep inbox evidence."""
        plan = execute_collaboration_plan("Implement a blocked offline code change.")

        self.assertEqual(plan.status, "blocked")
        self.assertEqual(plan.executions[-1].status, "blocked")
        self.assertIsNotNone(plan.runtime_session)
        assert plan.runtime_session is not None
        self.assertEqual(plan.runtime_session.status, "blocked")
        self.assertEqual(plan.runtime_session.active_role, "coding_agent")
        self.assertEqual(plan.runtime_session.transitions[-1].to_state, "blocked")
        self.assertEqual(plan.runtime_session.queue_items[-1].status, "blocked")
        self.assertEqual(plan.runtime_session.inbox_entries[-1].status, "blocked")
        self.assertEqual(plan.runtime_session.outbox_entries[-1].status, "blocked")
        self.assertEqual(plan.runtime_session.claim_records[-1].status, "blocked")

    def test_build_collaboration_plan_for_teacher_task(self) -> None:
        """Verify that build collaboration plan for teacher task."""
        plan = build_collaboration_plan("Explain RAG architecture.")

        self.assertIn("teacher_agent", plan.to_text())
        self.assertEqual([role["name"] for role in plan.to_dict()["assigned_roles"]], ["teacher_agent"])
        self.assertEqual(len(plan.to_dict()["delegations"]), 1)

    def test_route_to_list_skills(self) -> None:
        """Verify that route to list skills."""
        route = route_intent("List available skills.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "list_skills")

    def test_route_to_execute_skill(self) -> None:
        """Verify that route to execute skill."""
        route = route_intent("Execute skill for code review.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "execute_skill")

    def test_route_to_plan_subagents(self) -> None:
        """Verify that route to plan subagents."""
        route = route_intent("Plan subagent collaboration for a code review.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "plan_subagents")

    def test_route_to_execute_subagents(self) -> None:
        """Verify that route to execute subagents."""
        route = route_intent("Execute subagent collaboration for a code review.")

        self.assertEqual(route.action, "use_tool")
        self.assertEqual(route.tool_name, "execute_subagents")

    def test_agent_lists_skills(self) -> None:
        """Verify that agent lists skills."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("List available skills.")

        self.assertEqual(run.route.tool_name, "list_skills")
        self.assertIn("Available skills", run.answer)
        self.assertIn("professional-code-review", run.answer)

    def test_agent_plans_subagent_collaboration(self) -> None:
        """Verify that agent plans subagent collaboration."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Plan subagent collaboration for a code review.")

        self.assertEqual(run.route.tool_name, "plan_subagents")
        self.assertIn("Collaboration objective", run.answer)
        self.assertIn("Contracts:", run.answer)

    def test_agent_executes_subagent_collaboration(self) -> None:
        """Verify that agent executes subagent collaboration."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute subagent collaboration for a code review.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.tool_name, "execute_subagents")
        self.assertIn("Executions:", run.answer)
        self.assertIn("Returns:", run.answer)
        self.assertIsNotNone(trace["subagent_runtime"])
        self.assertEqual(trace["subagent_runtime"]["status"], "completed")
        self.assertEqual(trace["subagent_delegation"]["status"], "completed")

    def test_agent_executes_subagent_collaboration_failure_exports_recovery(self) -> None:
        """Verify that agent executes subagent collaboration failure exports recovery."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute subagent collaboration for an ambiguous underspecified code task.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.tool_name, "execute_subagents")
        self.assertEqual(trace["subagent_delegation"]["status"], "failed")
        self.assertEqual(trace["tool_result"]["metadata"]["recovery_plan"]["failure_type"], "delegation_failed")

    def test_agent_trace_dict_contains_subagent_delegation(self) -> None:
        """Verify that agent trace dict contains subagent delegation."""
        agent = WorkspaceAgent(Path("."))

        trace = agent.to_trace_dict(agent.run("Plan subagent collaboration for a code review."))

        self.assertIsNotNone(trace["subagent_delegation"])
        self.assertEqual(trace["subagent_delegation"]["delegations"][0]["role"]["name"], "teacher_agent")
        self.assertIn("delegation", [event["event_type"] for event in trace["runtime_events"]])

    def test_agent_trace_dict_contains_subagent_runtime(self) -> None:
        """Verify that agent trace dict contains subagent runtime."""
        agent = WorkspaceAgent(Path("."))

        trace = agent.to_trace_dict(agent.run("Execute subagent collaboration for a code review."))

        self.assertIsNotNone(trace["subagent_runtime"])
        self.assertEqual(trace["subagent_runtime"]["execution_mode"], "deterministic-async-delegation")
        self.assertIn("queue_items", trace["subagent_runtime"])
        self.assertIn("transitions", trace["subagent_runtime"])

    def test_agent_executes_skill(self) -> None:
        """Verify that agent executes skill."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute skill for code review.")

        self.assertEqual(run.route.tool_name, "execute_skill")
        self.assertIn("Skill run: code_review", run.answer)
        self.assertIn("Executed steps", run.answer)
        self.assertIn("tool-backed steps", run.answer)
        self.assertIn("[list_dir]", run.answer)

    def test_agent_trace_dict_contains_skill_run(self) -> None:
        """Verify that agent trace dict contains skill run."""
        agent = WorkspaceAgent(Path("."))

        trace = agent.to_trace_dict(agent.run("Execute skill for code review."))

        self.assertIsNotNone(trace["skill_run"])
        self.assertEqual(trace["skill_run"]["skill"]["name"], "code_review")
        self.assertEqual(trace["skill_run"]["skill"]["source"], "builtin")
        self.assertEqual(trace["skill_run"]["status"], "completed")
        self.assertEqual(trace["skill_run"]["tool_backed_steps"], 3)

    def test_agent_executes_project_skill(self) -> None:
        """Verify that agent executes project skill."""
        agent = WorkspaceAgent(Path("."))

        run = agent.run("Execute skill professional-code-review.")
        trace = agent.to_trace_dict(run)

        self.assertEqual(run.route.tool_name, "execute_skill")
        self.assertIn("Skill run: professional-code-review", run.answer)
        self.assertEqual(trace["skill_run"]["skill"]["source"], "project")

    def test_collaboration_demo_cli(self) -> None:
        """Verify that collaboration demo cli."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.collaboration_demo", "--task", "Review this code and add tests."],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Skill: code_review", result.stdout)
        self.assertIn("coding_agent", result.stdout)

    def test_collaboration_demo_executes_skill(self) -> None:
        """Verify that collaboration demo executes skill."""
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
        """Verify that collaboration demo executes tool backed skill."""
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
        """Verify that collaboration demo lists project skills."""
        result = subprocess.run(
            [sys.executable, "-m", "cli.collaboration_demo", "--list-skills"],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("professional-code-review", result.stdout)
        self.assertIn("Source: project", result.stdout)

    def test_collaboration_demo_executes_project_skill(self) -> None:
        """Verify that collaboration demo executes project skill."""
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

    def test_collaboration_demo_executes_subagents(self) -> None:
        """Verify that collaboration demo executes subagents."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Implement a bug fix and test it.",
                "--execute-subagents",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("Executions:", result.stdout)
        self.assertIn("Returns:", result.stdout)
        self.assertIn("Runtime session:", result.stdout)
        self.assertIn("Plan status: completed", result.stdout)

    def test_collaboration_demo_prints_runtime_json(self) -> None:
        """Verify that collaboration demo prints runtime json."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Implement a bug fix and test it.",
                "--execute-subagents",
                "--runtime-json",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("\"session_id\":", result.stdout)
        self.assertIn("\"messages\":", result.stdout)
        self.assertIn("\"transitions\":", result.stdout)

    def test_collaboration_demo_prints_queue_and_mailbox_json(self) -> None:
        """Verify that collaboration demo prints queue, inbox, and outbox json."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "cli.collaboration_demo",
                "--task",
                "Implement a blocked offline code change.",
                "--execute-subagents",
                "--queue-json",
                "--inbox-role",
                "coding_agent",
                "--outbox-role",
                "coding_agent",
            ],
            check=True,
            capture_output=True,
            text=True,
        )

        self.assertIn("\"queue_items\":", result.stdout)
        self.assertIn("\"inbox_entries\":", result.stdout)
        self.assertIn("\"outbox_entries\":", result.stdout)
        self.assertIn("\"claim_records\":", result.stdout)
        self.assertIn("\"status\": \"blocked\"", result.stdout)


if __name__ == "__main__":
    unittest.main()
