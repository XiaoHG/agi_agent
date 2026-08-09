"""Tests for long-horizon session and task memory."""

from pathlib import Path
import tempfile
import unittest

from agent import AgentMemoryStore, WorkspaceAgent


class MemoryTests(unittest.TestCase):
    """Verify session/task memory stays stable across persisted runs."""

    def test_memory_store_updates_session_and_task_from_trace(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            store = AgentMemoryStore(Path(tmp))
            snapshot = store.update_from_trace(
                "learning-session",
                "readme-task",
                {
                    "run_id": "run-1",
                    "user_input": "Read README.md.",
                    "route": {"action": "use_tool", "tool_name": "read_file"},
                    "tool_result": {"tool_name": "read_file"},
                    "skill_run": None,
                    "subagent_delegation": None,
                    "tool_error": None,
                    "answer_preview": "Result: read README.md.",
                },
            )

            session = store.load_session("learning-session")
            task = store.load_task("readme-task")

            self.assertEqual(snapshot.session_id, "learning-session")
            self.assertIsNotNone(session)
            self.assertIsNotNone(task)
            self.assertEqual(session.run_ids, ("run-1",))
            self.assertEqual(task.latest_run_id, "run-1")
            self.assertIn("Route: use_tool / read_file", session.key_facts)

    def test_workspace_agent_persists_memory_snapshot(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            history_dir = root / "history"
            memory_dir = root / "memory"
            agent = WorkspaceAgent(
                root,
                history_dir=history_dir,
                memory_dir=memory_dir,
                session_id="session-42",
                task_id="readme-learning",
            )

            run = agent.run("Read README.md and summarize the project learning goals.")
            trace = agent.to_trace_dict(run)

            self.assertEqual(trace["session_id"], "session-42")
            self.assertEqual(trace["task_id"], "readme-learning")
            self.assertIsNotNone(trace["memory"])
            self.assertEqual(trace["memory"]["session_id"], "session-42")
            self.assertEqual(trace["memory"]["task_id"], "readme-learning")
            self.assertIn("Session ID: session-42", agent.format_trace(run))

    def test_workspace_agent_formats_session_and_task_memory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "README.md").write_text("agent workflow\n", encoding="utf-8")
            agent = WorkspaceAgent(
                root,
                history_dir=root / "history",
                memory_dir=root / "memory",
                session_id="memory-session",
                task_id="memory-task",
            )
            agent.run("Read README.md.")

            session_text = agent.format_session_memory()
            task_text = agent.format_task_memory()

            self.assertIn("Session memory", session_text)
            self.assertIn("memory-session", session_text)
            self.assertIn("Task memory", task_text)
            self.assertIn("memory-task", task_text)


if __name__ == "__main__":
    unittest.main()
