# agent/

This directory contains the core agent implementation.

Appropriate contents:

- Minimal agent loop
- Tool calling
- Multi-step workflow
- State management
- Memory mechanisms
- Observability and error handling

The runtime code should evolve by capability module, not by weekly folders:

```text
agent/
  core.py
  router.py
  tools.py
  prompts.py
  state.py      # Add later when state management is needed.
  memory.py     # Add later when memory is needed.
```

## Current implementation

The current Python package uses standard module names and keeps the runtime code simple:

```text
agent/core.py
agent/router.py
agent/tool_calling.py
agent/tool_loop.py
agent/tool_schema.py
agent/tool_synthesis.py
agent/tools.py
agent/prompts.py
```

Core files:

- `core.py`: agent orchestration.
- `router.py`: tool-routing decision logic.
- `tool_calling.py`: LLM-assisted structured tool selection.
- `tool_loop.py`: bounded multi-step LLM tool loop records.
- `tool_schema.py`: workspace tool catalog and schema definitions.
- `tool_synthesis.py`: LLM final synthesis from tool-loop observations.
- `tools.py`: local tool implementations.
- `prompts.py`: prompt loading helpers.

Current tool families:

- File tools: read files, list directories, and count file lines.
- RAG tools: search local documents and answer with grounded LLM context.
- MCP tools: list MCP tools, summarize the workspace, and read project files through the MCP adapter.
- Skills tools: list reusable skills and select a skill plan for a task.
- Subagent tools: list project subagents and plan collaboration.
