"""Tests for normalized runtime events."""

import unittest

from agent import AgentStep, RuntimeEvent, build_runtime_events


class RuntimeEventTests(unittest.TestCase):
    """Verify runtime events are exported as stable structured trace data."""

    def test_runtime_event_exports_dict_and_text(self) -> None:
        event = RuntimeEvent(1, "step", "Route request", "graph / langgraph_workflow")

        self.assertEqual(event.to_dict()["event_type"], "step")
        self.assertIn("[step]", event.to_text())

    def test_build_runtime_events_from_steps(self) -> None:
        events = build_runtime_events(
            [
                AgentStep("Receive input", "Read README.md."),
                AgentStep("Route request", "use_tool / read_file"),
            ]
        )

        self.assertEqual(len(events), 2)
        self.assertEqual(events[0].event_type, "step")
        self.assertEqual(events[1].name, "Route request")

    def test_build_runtime_events_includes_graph_and_recovery(self) -> None:
        events = build_runtime_events(
            [AgentStep("Run graph", "route=read_file")],
            {
                "graph_route": "read_file",
                "graph_steps": ["route", "call_tool", "recover_tool_failure", "finalize"],
                "recovery_plan": {
                    "status": "failed",
                    "failure_type": "missing_resource",
                    "reason": "File does not exist: missing.md",
                },
            },
        )

        event_types = [event.event_type for event in events]

        self.assertIn("graph", event_types)
        self.assertIn("recovery", event_types)

    def test_build_runtime_events_includes_skill_and_error(self) -> None:
        events = build_runtime_events(
            [AgentStep("Run graph", "route=skill_execution")],
            {
                "skill_run": {
                    "status": "completed",
                    "skill": {"name": "code_review"},
                },
            },
            "Tool failed.",
        )

        event_types = [event.event_type for event in events]

        self.assertIn("skill", event_types)
        self.assertIn("error", event_types)

    def test_build_runtime_events_includes_delegation_execution(self) -> None:
        events = build_runtime_events(
            [AgentStep("Run graph", "route=execute_subagents")],
            {
                "subagent_delegation": {
                    "status": "completed",
                    "delegations": [{"role": {"name": "teacher_agent"}}, {"role": {"name": "coding_agent"}}],
                    "executions": [{"role_name": "teacher_agent"}, {"role_name": "coding_agent"}],
                },
            },
        )

        event_types = [event.event_type for event in events]

        self.assertIn("delegation", event_types)
        self.assertIn("delegation_execution", event_types)


if __name__ == "__main__":
    unittest.main()
