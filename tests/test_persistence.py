"""Tests for checkpoint and run persistence."""

from contextlib import redirect_stdout
import io
from pathlib import Path
import tempfile
import unittest

from agent import WorkspaceAgent, build_run_checkpoint, load_checkpoint
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
            self.assertIn("Route:", output.getvalue())

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


if __name__ == "__main__":
    unittest.main()
