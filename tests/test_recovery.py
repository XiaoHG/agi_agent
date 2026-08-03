"""Tests for unified recovery plan models."""

import unittest

from agent import (
    RecoveryPlan,
    build_exception_recovery_plan,
    build_skill_recovery_plan,
    build_tool_recovery_plan,
    classify_failure,
)


class RecoveryPlanTests(unittest.TestCase):
    """Verify recovery plans stay stable across tool and skill failures."""

    def test_tool_recovery_plan_exports_dict_and_text(self) -> None:
        plan = build_tool_recovery_plan(
            "read_workspace_file",
            {"path": "missing.md"},
            "File does not exist: missing.md",
        )

        data = plan.to_dict()

        self.assertEqual(data["source_type"], "tool")
        self.assertEqual(data["source_name"], "read_workspace_file")
        self.assertEqual(data["failure_type"], "missing_resource")
        self.assertEqual(data["tool_input"], {"path": "missing.md"})
        self.assertIn("Tool recovery plan", plan.to_text())

    def test_skill_recovery_plan_exports_failed_step_context(self) -> None:
        skill_run = {
            "skill": {"name": "learning_explanation"},
            "status": "failed",
            "completed_steps": 2,
            "steps": [
                {"index": 1, "status": "completed", "instruction": "Clarify"},
                {
                    "index": 2,
                    "status": "failed",
                    "instruction": "Read learning state.",
                    "tool_name": "read_file",
                    "tool_input": "docs/current-learning-state.md",
                    "error": "File does not exist: docs/current-learning-state.md",
                },
            ],
        }

        plan = build_skill_recovery_plan(skill_run)
        data = plan.to_dict()

        self.assertEqual(data["source_type"], "skill")
        self.assertEqual(data["source_name"], "learning_explanation")
        self.assertEqual(data["skill_name"], "learning_explanation")
        self.assertEqual(data["tool_name"], "read_file")
        self.assertEqual(data["tool_input"], {"value": "docs/current-learning-state.md"})
        self.assertEqual(data["completed_steps"], 2)
        self.assertIn("Skill recovery plan", plan.to_text())

    def test_exception_recovery_plan_uses_exception_source(self) -> None:
        plan = build_exception_recovery_plan("Network connection failed.", "answer_docs_with_llm")

        self.assertEqual(plan.source_type, "exception")
        self.assertEqual(plan.source_name, "answer_docs_with_llm")
        self.assertEqual(plan.failure_type, "external_dependency")
        self.assertIn("Tool recovery plan", plan.to_text())

    def test_classify_failure_maps_common_cases(self) -> None:
        self.assertEqual(classify_failure("File does not exist: README.md"), "missing_resource")
        self.assertEqual(classify_failure("Path escapes workspace root"), "unsafe_or_denied_access")
        self.assertEqual(classify_failure("Missing API key"), "external_dependency")
        self.assertEqual(classify_failure("File is too large"), "input_too_large")
        self.assertEqual(classify_failure("Unexpected failure"), "execution_error")

    def test_recovery_plan_allows_optional_context(self) -> None:
        plan = RecoveryPlan(
            status="failed",
            failure_type="execution_error",
            source_type="tool",
            source_name="demo_tool",
            reason="Unexpected failure",
            next_safe_action="Inspect the failure.",
        )

        data = plan.to_dict()

        self.assertIsNone(data["tool_name"])
        self.assertIsNone(data["skill_name"])
        self.assertIsNone(data["failed_step"])


if __name__ == "__main__":
    unittest.main()
