"""Tests for the comprehensive project learning assistant."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import unittest

from agent.project import ProjectLearningAssistant
from cli import project_demo


class ProjectLearningAssistantTests(unittest.TestCase):
    """Verify the project-level assistant coordinates existing capabilities."""

    def test_project_assistant_runs_capability_chain(self) -> None:
        """Verify that project assistant runs capability chain."""
        assistant = ProjectLearningAssistant(Path("."))

        report = assistant.run("Verify the project learning assistant.")

        self.assertEqual(report.regression_report["failed"], 0)
        self.assertIn("agi_agent", report.readme_summary)
        self.assertIn("relevant local context", report.docs_context)
        self.assertIn("Workspace", report.mcp_summary)
        self.assertIn("Skill:", report.skill_plan)
        self.assertIn("Collaboration objective", report.collaboration_plan)

    def test_project_report_renders_summary(self) -> None:
        """Verify that project report renders summary."""
        assistant = ProjectLearningAssistant(Path("."))

        text = assistant.run().to_text()

        self.assertIn("Capability chain", text)
        self.assertIn("Regression eval", text)
        self.assertIn("Failed: 0", text)

    def test_project_demo_cli(self) -> None:
        """Verify that project demo cli."""
        output = io.StringIO()

        with redirect_stdout(output):
            exit_code = project_demo.main(["--objective", "Verify project demo."])

        self.assertEqual(exit_code, 0)
        self.assertIn("Capability chain", output.getvalue())


if __name__ == "__main__":
    unittest.main()
