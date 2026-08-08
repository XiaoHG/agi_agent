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

Resume one saved run by id:

```bash
python -m cli.main --resume-run abc12345
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
