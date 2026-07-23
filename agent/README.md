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
agent/tools.py
agent/prompts.py
```

Core files:

- `core.py`: agent orchestration.
- `router.py`: tool-routing decision logic.
- `tools.py`: local tool implementations.
- `prompts.py`: prompt loading helpers.

