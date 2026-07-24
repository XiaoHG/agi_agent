# State and Workflow v2

Version: v2

Date: 2026-07-24

## Goal

This iteration adds the first multi-step execution layer on top of the minimal agent loop.

The new layer introduces:

- mutable execution state
- simple workflow planning
- sequential tool execution
- workflow-level answer synthesis

## New files

### `agent/state.py`

New file.

Exact line range: `1-53`

Responsibilities:

- define `AgentStep`
- define `AgentState`
- record trace steps
- record tool results
- expose helper methods for state updates

### `agent/workflow.py`

New file.

Exact line range: `1-178`

Responsibilities:

- define `WorkflowStep`
- define `WorkflowPlan`
- build a small ordered plan from user input
- synthesize workflow results into a final answer

### `versions/README.md`

New file.

Exact line range: `1-19`

Responsibilities:

- define how iteration notes should be stored
- enforce the `*_v2.md` / `*_v3.md` naming pattern

## Modified files

### `agent/core.py`

Changed line ranges:

- imports and workflow integration: `11-12`, `50-63`, `85-128`
- existing single-step flow remains unchanged outside those ranges

What changed:

- imports now include `AgentState` and workflow helpers
- `WorkspaceAgent.run()` now checks for `workflow` routes
- new `_run_workflow()` execution path was added
- workflow failures are handled separately
- workflow results are synthesized into a final answer

New behavior:

1. Receive input
2. Load prompts
3. Route request
4. If the route is `workflow`, build a workflow plan
5. Execute each workflow step in order
6. Record tool results in mutable state
7. Synthesize a final answer from the collected results

### `agent/router.py`

Changed line ranges:

- workflow detection helper: `80-94`
- workflow routing branch: `115-120`

What changed:

- added `_looks_like_workflow_request()`
- added a new `workflow` route

New behavior:

- requests containing ordered-action markers such as `and then`, `then`, `after that`, or `step by step` are routed to the workflow path

### `agent/__init__.py`

Changed line ranges:

- exports: `3-6`, `8-20`

What changed:

- exported `AgentState`
- exported `AgentStep` from `agent.state`

### `tests/test_agent.py`

Changed line ranges:

- workflow tests: `32-42`

What changed:

- added workflow routing coverage
- added a workflow execution test

## New interaction flow

### Single-step flow

```text
input -> route -> direct answer or one tool -> answer
```

### Workflow flow

```text
input -> route(workflow) -> plan -> step 1 -> step 2 -> synthesis -> answer
```

## Example workflow

Input:

```text
Read README.md and then count lines.
```

Expected behavior:

- route to `workflow`
- read the file
- count lines
- synthesize a combined answer

## Verification

Run:

```bash
python -m unittest discover -s tests -v
python -m cli.main --input "Read README.md and then count lines." --trace
```

Observed result:

- tests pass
- workflow route is triggered
- workflow trace is visible
- tool results are collected and summarized

## Notes for future iterations

- Keep version notes in `versions/`
- Use the same `*_v2.md`, `*_v3.md` pattern for future iteration reports
- Add more workflow patterns in later versions instead of making this planner too complex too early
