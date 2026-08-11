"""Tests for checkpoint and run persistence."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from agent import WorkspaceAgent, build_run_checkpoint, load_checkpoint
from agent.replay import (
    build_checkpoint_resume_plan,
    build_checkpoint_resume_report,
    build_replay_report,
    compare_replay_reports,
    format_checkpoint_resume_report,
    format_replay_diff_report,
    format_replay_report,
)
from agent.persistence import RunCheckpointStore
from cli import main as cli_main
from cli import langgraph_demo


class PersistenceTests(unittest.TestCase):
    """Verify run checkpoints can be saved, loaded, and displayed."""

    def test_checkpoint_store_saves_and_loads_latest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            history_dir = Path(tmp) / "runs"
            store = RunCheckpointStore(history_dir)
            record = build_run_checkpoint(
                run_id="abc12345",
                run_kind="graph",
                user_input="Read README.md.",
                route={"action": "graph", "tool_name": "langgraph_workflow"},
                steps=[{"title": "Run graph", "detail": "route=read_file"}],
                answer="Graph answer",
                trace={"route": {"action": "graph"}},
                trace_text="Run ID: abc12345",
            )

            saved_path = store.save(record)
            latest = store.load_latest()

            self.assertEqual(saved_path.name, "abc12345.json")
            self.assertEqual(latest["run_id"], "abc12345")
            self.assertTrue((history_dir / "latest.json").exists())
            self.assertEqual(load_checkpoint(saved_path)["run_kind"], "graph")

    def test_workspace_agent_persists_graph_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)

            run = agent.run("Use LangGraph to read README.md.")
            latest = load_checkpoint(history_dir / "latest.json")

            self.assertIsNotNone(latest)
            self.assertEqual(latest["run_id"], run.run_id)
            self.assertEqual(latest["run_kind"], "graph")
            self.assertEqual(latest["trace"]["route"]["action"], "graph")
            self.assertEqual(latest["trace"]["tool_result"]["metadata"]["graph_route"], "read_file")
            self.assertIn("[Runtime Events]", latest["trace_text"])

    def test_workspace_agent_persists_workflow_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)

            run = agent.run("Read README.md and then count lines.")
            latest = load_checkpoint(history_dir / "latest.json")

            self.assertIsNotNone(latest)
            self.assertEqual(latest["run_id"], run.run_id)
            self.assertEqual(latest["run_kind"], "workflow")
            self.assertEqual(latest["trace"]["route"]["action"], "workflow")

    def test_cli_main_can_show_last_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--show-last-run",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Run ID:", output.getvalue())
            self.assertIn("Session ID:", output.getvalue())
            self.assertIn("Route:", output.getvalue())

    def test_cli_main_can_list_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")
            agent.run("Read README.md and then count lines.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--list-runs",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("1.", output.getvalue())
            self.assertIn("graph", output.getvalue())

    def test_cli_main_can_show_run_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            run = agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--show-run",
                        run.run_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn(run.run_id, output.getvalue())
            self.assertIn("Run kind:", output.getvalue())

    def test_langgraph_demo_persists_graph_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "graph-history"

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = langgraph_demo.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--question",
                        "Read README.md.",
                    ]
                )

            latest = load_checkpoint(history_dir / "latest.json")

            self.assertEqual(exit_code, 0)
            self.assertIsNotNone(latest)
            self.assertEqual(latest["run_kind"], "graph")
            self.assertEqual(latest["route"]["action"], "read_file")
            self.assertEqual(latest["trace"]["selected_tool"], "read_workspace_file")

    def test_replay_report_rebuilds_runtime_events(self) -> None:
        record = {
            "run_id": "abc12345",
            "run_kind": "graph",
            "created_at": "2026-08-07T00:00:00+00:00",
            "user_input": "Read README.md.",
            "route": {"action": "graph", "tool_name": "langgraph_workflow"},
            "answer": "Graph answer",
            "trace_text": "trace text",
            "trace": {
                "route": {"action": "graph"},
                "steps": [
                    {"title": "Receive input", "detail": "Read README.md."},
                    {"title": "Run graph", "detail": "route=read_file"},
                ],
                "tool_result": {
                    "metadata": {
                        "graph_route": "read_file",
                    }
                },
                "runtime_events": [
                    {"index": 1, "event_type": "step", "name": "Receive input", "detail": "Read README.md.", "payload": {}},
                ],
            },
        }

        report = build_replay_report(record)
        rendered = format_replay_report(record)

        self.assertEqual(report.run_id, "abc12345")
        self.assertGreaterEqual(len(report.events), 2)
        self.assertEqual(report.events[0].name, "Receive input")
        self.assertIn("Replay report", rendered)
        self.assertIn("Rebuilt runtime events:", rendered)
        self.assertIn("Graph route", rendered)

    def test_workspace_agent_replays_latest_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")

            replay_text = agent.replay_latest_checkpoint()

            self.assertIn("Replay report", replay_text)
            self.assertIn("Runtime events:", replay_text)
            self.assertIn("Answer:", replay_text)

    def test_replay_diff_report_compares_two_runs(self) -> None:
        older = {
            "run_id": "run-old",
            "run_kind": "graph",
            "created_at": "2026-08-07T00:00:00+00:00",
            "user_input": "Read README.md.",
            "route": {"action": "graph", "tool_name": "langgraph_workflow"},
            "answer": "Older answer",
            "trace_text": "older trace",
            "trace": {
                "route": {"action": "graph", "tool_name": "langgraph_workflow"},
                "selected_tool": "read_workspace_file",
                "logical_tool_name": "read_file",
                "steps": [
                    {"title": "Receive input", "detail": "Read README.md."},
                    {"title": "Run graph", "detail": "route=read_file"},
                ],
                "tool_result": {
                    "tool_name": "langgraph_workflow",
                    "metadata": {
                        "graph_route": "read_file",
                    }
                },
            },
        }
        newer = {
            "run_id": "run-new",
            "run_kind": "graph",
            "created_at": "2026-08-07T00:01:00+00:00",
            "user_input": "List project skills.",
            "route": {"action": "graph", "tool_name": "langgraph_workflow"},
            "answer": "Newer answer",
            "trace_text": "newer trace",
            "trace": {
                "route": {"action": "graph", "tool_name": "langgraph_workflow"},
                "selected_tool": "execute_project_skill",
                "logical_tool_name": "execute_skill",
                "steps": [
                    {"title": "Receive input", "detail": "List project skills."},
                    {"title": "Run graph", "detail": "route=skill_execution"},
                    {"title": "Record skill", "detail": "status=completed"},
                ],
                "tool_result": {
                    "tool_name": "langgraph_workflow",
                    "metadata": {
                        "graph_route": "skill_execution",
                        "skill_run": {
                            "status": "completed",
                            "skill": {"name": "code_review"},
                        },
                    }
                },
            },
        }

        report = compare_replay_reports(older, newer)
        rendered = format_replay_diff_report(older, newer)

        self.assertIn("graph_route", report.changed_fields)
        self.assertIn("answer", report.changed_fields)
        self.assertIn("tool_usage", report.changed_fields)
        self.assertIn("skill_usage", report.changed_fields)
        self.assertEqual(report.tool_names_added, ("execute_project_skill", "execute_skill"))
        self.assertEqual(report.skill_names_added, ("code_review",))
        self.assertIn("Replay diff report", rendered)
        self.assertIn("Tools added:", rendered)
        self.assertIn("Skills added:", rendered)

    def test_workspace_agent_compares_latest_two_checkpoints(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")
            agent.run("Read README.md and then count lines.")

            diff_text = agent.compare_latest_two_checkpoints()

            self.assertIn("Replay diff report", diff_text)
            self.assertIn("Older run:", diff_text)
            self.assertIn("Newer run:", diff_text)
            self.assertIn("Differences:", diff_text)

    def test_checkpoint_resume_report_uses_resume_plan(self) -> None:
        record = {
            "run_id": "run-resume",
            "run_kind": "graph",
            "created_at": "2026-08-07T00:00:00+00:00",
            "user_input": "Use LangGraph to read README.md.",
            "route": {"action": "graph", "tool_name": "langgraph_workflow", "tool_input": None, "reason": "graph"},
            "answer": "Graph answer",
            "trace_text": "trace text",
            "trace": {
                "route": {"action": "graph", "tool_name": "langgraph_workflow"},
                "steps": [{"title": "Run graph", "detail": "route=read_file"}],
                "tool_result": {
                    "metadata": {
                        "graph_route": "read_file",
                    }
                },
            },
        }

        plan = build_checkpoint_resume_plan(record)
        report = build_checkpoint_resume_report(record)
        rendered = format_checkpoint_resume_report(record)

        self.assertEqual(plan.source_run_id, "run-resume")
        self.assertEqual(plan.resume_mode, "checkpoint_rerun")
        self.assertTrue(plan.can_resume)
        self.assertEqual(plan.branch_session_id, "default")
        self.assertEqual(plan.branch_task_id, "unknown")
        self.assertEqual(plan.branch_depth, 1)
        self.assertIn("Checkpoint resume plan", plan.to_text())
        self.assertIn("Branch depth: 1", plan.to_text())
        self.assertIn("Checkpoint resume plan", report.to_text())
        self.assertIn("Source summary:", rendered)
        self.assertIn("Resume mode:", rendered)

    def test_workspace_agent_can_resume_latest_checkpoint(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            memory_dir = root / "memory"
            agent = WorkspaceAgent(
                root,
                history_dir=history_dir,
                memory_dir=memory_dir,
                session_id="resume-session",
                task_id="resume-task",
            )
            source_run = agent.run("Use LangGraph to read README.md.")

            resume_text = agent.resume_latest_checkpoint()
            resumed = load_checkpoint(history_dir / "latest.json")

            self.assertIn("Checkpoint resume plan", resume_text)
            self.assertIn("Session / Task: resume-session / resume-task", resume_text)
            self.assertIn("Source summary:", resume_text)
            self.assertIn("Branch depth: 1", resume_text)
            self.assertIsNotNone(resumed)
            self.assertNotEqual(resumed["run_id"], source_run.run_id)
            self.assertEqual(resumed["resume"]["source_run_id"], source_run.run_id)
            self.assertEqual(resumed["resume"]["branch_depth"], 1)
            self.assertEqual(resumed["trace"]["resume"]["source_run_id"], source_run.run_id)

    def test_resume_branch_increments_depth_for_nested_resume(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir, session_id="branch-session", task_id="branch-task")

            source_run = agent.run("Use LangGraph to read README.md.")
            agent.resume_latest_checkpoint()
            first_branch = load_checkpoint(history_dir / "latest.json")
            self.assertIsNotNone(first_branch)

            agent.resume_latest_checkpoint()
            second_branch = load_checkpoint(history_dir / "latest.json")

            self.assertIsNotNone(second_branch)
            self.assertEqual(first_branch["resume"]["source_run_id"], source_run.run_id)
            self.assertEqual(first_branch["resume"]["branch_depth"], 1)
            self.assertEqual(second_branch["resume"]["branch_depth"], 2)
            self.assertEqual(second_branch["resume"]["source_run_id"], first_branch["run_id"])

    def test_cli_main_can_show_session_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            memory_dir = root / "memory"
            agent = WorkspaceAgent(
                root,
                history_dir=history_dir,
                memory_dir=memory_dir,
                session_id="cli-session",
                task_id="cli-task",
            )
            agent.run("Read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--memory-dir",
                        str(memory_dir),
                        "--session-id",
                        "cli-session",
                        "--show-session-memory",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Session memory", output.getvalue())
            self.assertIn("cli-session", output.getvalue())

    def test_cli_main_can_show_task_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            memory_dir = root / "memory"
            agent = WorkspaceAgent(
                root,
                history_dir=history_dir,
                memory_dir=memory_dir,
                session_id="cli-session",
                task_id="cli-task",
            )
            agent.run("Read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--memory-dir",
                        str(memory_dir),
                        "--task-id",
                        "cli-task",
                        "--show-task-memory",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Task memory", output.getvalue())
            self.assertIn("cli-task", output.getvalue())

    def test_cli_main_can_resume_last_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--resume-last-run",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Checkpoint resume plan", output.getvalue())
            self.assertIn("Resume diff:", output.getvalue())
            self.assertIn("Branch depth:", output.getvalue())

    def test_cli_main_can_resume_run_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            run = agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--resume-run",
                        run.run_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn(run.run_id, output.getvalue())
            self.assertIn("Checkpoint resume plan", output.getvalue())
            self.assertIn("Branch depth:", output.getvalue())

    def test_cli_main_can_replay_last_run(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--replay-last-run",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Replay report", output.getvalue())
            self.assertIn("Rebuilt runtime events:", output.getvalue())

    def test_cli_main_can_replay_run_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            run = agent.run("Use LangGraph to read README.md.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--replay-run",
                        run.run_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn(run.run_id, output.getvalue())
            self.assertIn("Graph route:", output.getvalue())

    def test_cli_main_can_compare_last_two_runs(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            agent.run("Use LangGraph to read README.md.")
            agent.run("Read README.md and then count lines.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--compare-last-two-runs",
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn("Replay diff report", output.getvalue())
            self.assertIn("Step count delta:", output.getvalue())

    def test_cli_main_can_compare_runs_by_id(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            agent = WorkspaceAgent(root, history_dir=history_dir)
            first_run = agent.run("Use LangGraph to read README.md.")
            second_run = agent.run("Read README.md and then count lines.")

            output = io.StringIO()
            with redirect_stdout(output):
                exit_code = cli_main.main(
                    [
                        "--root",
                        str(root),
                        "--history-dir",
                        str(history_dir),
                        "--compare-runs",
                        first_run.run_id,
                        second_run.run_id,
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertIn(first_run.run_id, output.getvalue())
            self.assertIn(second_run.run_id, output.getvalue())
            self.assertIn("Differences:", output.getvalue())


if __name__ == "__main__":
    unittest.main()
