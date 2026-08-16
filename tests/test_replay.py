"""Tests for replay summaries and diffs."""

import unittest

from agent import build_replay_summary, compare_replay_reports


class ReplayTests(unittest.TestCase):
    """Verify replay reports keep delegation metadata stable."""

    def test_replay_summary_collects_delegation_names(self) -> None:
        """Verify that replay summary collects delegation names."""
        record = {
            "run_id": "demo",
            "run_kind": "tool",
            "created_at": "2026-08-09T00:00:00Z",
            "user_input": "Plan subagent collaboration for a code review.",
            "route": {"action": "use_tool", "tool_name": "plan_subagents"},
            "steps": [{"title": "Route request", "detail": "use_tool / plan_subagents"}],
            "answer": "done",
            "trace": {
                "route": {"action": "use_tool", "tool_name": "plan_subagents"},
                "steps": [{"title": "Route request", "detail": "use_tool / plan_subagents"}],
                "tool_result": {
                    "tool_name": "plan_subagents",
                    "metadata": {
                        "subagent_delegation": {
                            "objective": "Plan subagent collaboration for a code review.",
                            "delegations": [
                                {"role": {"name": "teacher_agent"}},
                                {"role": {"name": "coding_agent"}},
                            ],
                        }
                    },
                },
            },
        }

        summary = build_replay_summary(record)

        self.assertEqual(summary.delegation_names, ("coding_agent", "teacher_agent"))

    def test_replay_diff_reports_delegation_changes(self) -> None:
        """Verify that replay diff reports delegation changes."""
        older = {
            "run_id": "old",
            "run_kind": "tool",
            "created_at": "2026-08-09T00:00:00Z",
            "user_input": "Explain RAG architecture.",
            "route": {"action": "use_tool", "tool_name": "plan_subagents"},
            "steps": [],
            "answer": "old",
            "trace": {
                "route": {"action": "use_tool", "tool_name": "plan_subagents"},
                "steps": [],
                "tool_result": {
                    "tool_name": "plan_subagents",
                    "metadata": {
                        "subagent_delegation": {
                            "objective": "Explain RAG architecture.",
                            "delegations": [{"role": {"name": "teacher_agent"}}],
                        }
                    },
                },
            },
        }
        newer = {
            "run_id": "new",
            "run_kind": "tool",
            "created_at": "2026-08-09T00:00:00Z",
            "user_input": "Review this code and add tests.",
            "route": {"action": "use_tool", "tool_name": "plan_subagents"},
            "steps": [],
            "answer": "new",
            "trace": {
                "route": {"action": "use_tool", "tool_name": "plan_subagents"},
                "steps": [],
                "tool_result": {
                    "tool_name": "plan_subagents",
                    "metadata": {
                        "subagent_delegation": {
                            "objective": "Review this code and add tests.",
                            "delegations": [
                                {"role": {"name": "teacher_agent"}},
                                {"role": {"name": "coding_agent"}},
                            ],
                        }
                    },
                },
            },
        }

        report = compare_replay_reports(older, newer)

        self.assertIn("delegation_usage", report.changed_fields)
        self.assertEqual(report.delegation_names_added, ("coding_agent",))

    def test_replay_summary_keeps_delegation_execution_metadata(self) -> None:
        """Verify that replay summary keeps delegation execution metadata."""
        record = {
            "run_id": "demo",
            "run_kind": "tool",
            "created_at": "2026-08-13T00:00:00Z",
            "user_input": "Execute subagent collaboration for a code review.",
            "route": {"action": "use_tool", "tool_name": "execute_subagents"},
            "steps": [{"title": "Route request", "detail": "use_tool / execute_subagents"}],
            "answer": "done",
            "trace": {
                "route": {"action": "use_tool", "tool_name": "execute_subagents"},
                "steps": [{"title": "Route request", "detail": "use_tool / execute_subagents"}],
                "tool_result": {
                    "tool_name": "execute_subagents",
                    "metadata": {
                        "subagent_delegation": {
                            "objective": "Execute subagent collaboration for a code review.",
                            "status": "completed",
                            "delegations": [
                                {"role": {"name": "teacher_agent"}},
                                {"role": {"name": "coding_agent"}},
                            ],
                            "executions": [
                                {"role_name": "teacher_agent", "status": "completed"},
                                {"role_name": "coding_agent", "status": "completed"},
                            ],
                        }
                    },
                },
            },
        }

        summary = build_replay_summary(record)

        self.assertEqual(summary.delegation_names, ("coding_agent", "teacher_agent"))


if __name__ == "__main__":
    unittest.main()
