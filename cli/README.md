# cli/

This directory contains command-line entrypoints and local debugging entrypoints.

Appropriate contents:

- `python -m ...` or `node ...` wrappers
- Interactive CLI entrypoints
- Demo runners
- Local debugging commands

Do not put core business logic here. CLI modules should only parse arguments, load configuration, and call capabilities from `agent/`.

## Current entrypoint

Run the agent:

```bash
python -m cli.main --input "Explain the difference between an agent and a chatbot."
```

For direct-answer requests, the main runtime now prefers an LLM-first answer path and keeps a deterministic fallback when the direct-answer model is unavailable.

Run with trace output:

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
```

Run the main agent with real DeepSeek planning for LangGraph requests:

```bash
python -m cli.main --input "Use LangGraph to read README.md." --llm-planner --trace
```

Run the default LangGraph-backed main runtime:

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
```

Run a multi-step workflow through the default LangGraph runtime:

```bash
python -m cli.main --input "Read README.md and then count lines." --trace
```

Compare against the classic pre-graph runtime:

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --classic-runtime --trace
```

Compare the workflow against the classic runtime:

```bash
python -m cli.main --input "Read README.md and then count lines." --classic-runtime --trace
```

Show the latest persisted run:

```bash
python -m cli.main --show-last-run --trace
```

List recent saved runs:

```bash
python -m cli.main --list-runs
```

Recent history now includes `branch_parent` and `depth`, so resumed runs can be inspected as formal checkpoint branches.

Show one saved run by id:

```bash
python -m cli.main --show-run abc12345 --trace
```

Replay the latest saved run:

```bash
python -m cli.main --replay-last-run
```

Replay one saved run by id:

```bash
python -m cli.main --replay-run abc12345
```

Resume the latest saved run:

```bash
python -m cli.main --resume-last-run
```

The resumed run is persisted as a new branch of the source checkpoint instead of overwriting the original history.

Resume one saved run by id:

```bash
python -m cli.main --resume-run abc12345
```

Run with explicit session/task continuity:

```bash
python -m cli.main --input "Read README.md." --session-id learning-session --task-id readme-learning
```

List stored session memory:

```bash
python -m cli.main --list-session-memory
```

Show one session memory record:

```bash
python -m cli.main --session-id learning-session --show-session-memory
```

List stored task memory:

```bash
python -m cli.main --list-task-memory
```

Show one task memory record:

```bash
python -m cli.main --task-id readme-learning --show-task-memory
```

Compare the latest two saved runs:

```bash
python -m cli.main --compare-last-two-runs
```

Compare two saved runs by id:

```bash
python -m cli.main --compare-runs abc12345 def67890
```

Run LLM tool calling:

```bash
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
```

Run tool calling through the default LangGraph-backed main runtime:

```bash
python -m cli.main --input "Use tool calling to read README.md." --trace
```

Compare tool calling against the classic runtime:

```bash
python -m cli.main --input "Use tool calling to read README.md." --classic-runtime --trace
```

Run a bounded LLM tool loop:

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```

Run tool loop through the default LangGraph-backed main runtime:

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --trace
```

Compare tool loop against the classic runtime:

```bash
python -m cli.main --input "Use tool loop to read README.md and then answer." --classic-runtime --trace
```

Run a LangGraph demo with checkpoint persistence:

```bash
python -m cli.langgraph_demo --question "Read README.md."
```

Run the LangGraph demo with the real DeepSeek planner:

```bash
python -m cli.langgraph_demo --question "Read README.md." --llm-planner
```

Rebuild the local RAG vector index:

```bash
python -m cli.rag_index_demo --question "agent workflow"
```

List local MCP tools with permission classes:

```bash
python -m cli.mcp_demo --list-tools
```

Attempt an MCP write with the default read-only policy:

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp"
```

Allow the MCP write tool explicitly:

```bash
python -m cli.mcp_demo --tool write_project_file --path notes.txt --content "hello mcp" --allow-write
```

Show the standardized MCP execution record:

```bash
python -m cli.mcp_demo --tool workspace_summary --show-execution
```

List skills with a runtime policy:

```bash
python -m cli.collaboration_demo --list-skills --skill-policy project-only
```

Block a project skill under a builtin-only policy:

```bash
python -m cli.collaboration_demo --task "Execute skill professional-code-review." --execute-skill --skill professional-code-review --skill-policy builtin-only
```

Run the main agent with a skill policy:

```bash
python -m cli.main --input "Execute skill professional-code-review." --skill-policy project-only
```

Run the industrial eval matrix:

```bash
python -m cli.eval_runner --matrix evals/industrial_eval_matrix.json
```

Run the industrial failure bench:

```bash
python -m cli.eval_runner --failure-bench evals/industrial_failure_bench.json
```

Run the release gate:

```bash
python -m cli.release_gate
```
