# Week 1 Eval Cases: Minimal CLI Agent

Status: implemented; extend as the agent evolves.

## Case 1: direct answer

Target capability: answer directly when no tool is needed.

Input:

```text
Explain the difference between an agent and a chatbot.
```

Expected behavior:

- Do not call file tools.
- Explain the core difference: task orientation, tool use, multi-step execution, and state.
- Produce a clear response.

Rejected behavior:

- Force a file-tool call.
- Give a vague answer such as "agents are smarter."

Actual output record:

```text
The main difference is that an agent makes task-oriented decisions, can call tools, can keep state, and can complete work through multiple steps.
```

Result: pass

## Case 2: read README

Target capability: select `read_file` when the user asks for a file.

Input:

```text
Read README.md and summarize the project learning goals.
```

Expected behavior:

- Call `read_file`.
- Base the answer on README.md.
- Do not invent content that is not in the file.

Rejected behavior:

- Invent content without reading the file.
- Pretend the read succeeded after a tool failure.

Actual output record:

```text
Result: read README.md.
Key content:
[read_file] README.md
# agi_agent
...
```

Result: pass

## Case 3: list project directories

Target capability: select `list_dir` for project structure questions.

Input:

```text
List the main project directories and explain what they are responsible for.
```

Expected behavior:

- Call `list_dir`.
- List the main project directories.
- Explain known directory responsibilities.

Rejected behavior:

- Answer only from memory.
- Omit key directories.

Actual output record:

```text
Result: inspected the current directory structure.
Responsibilities:
- agent/: Core agent loop experiments, including workflow, state, and tool calling.
- cli/: Command-line entrypoints for running and debugging the agent locally.
...
```

Result: pass

## Case 4: missing file

Target capability: handle tool failure.

Input:

```text
Read not-exist.md.
```

Expected behavior:

- Call `read_file`.
- Clearly report that the file does not exist.
- Do not crash.
- Do not invent file content.

Rejected behavior:

- Expose a raw traceback to the user.
- Invent content for the missing file.

Actual output record:

```text
Result: the tool call failed, so the task was not completed.
Reason: File does not exist: not-exist.md
```

Result: pass

