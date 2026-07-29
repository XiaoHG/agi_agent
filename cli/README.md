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

Run with trace output:

```bash
python -m cli.main --input "Read README.md and summarize the project learning goals." --trace
```

Run LLM tool calling:

```bash
python -m cli.tool_calling_demo --input "Use tool calling to read README.md." --trace
```

Run a bounded LLM tool loop:

```bash
python -m cli.tool_loop_demo --input "Use tool loop to count lines in README.md and then answer." --trace
```
