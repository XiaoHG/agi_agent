---
name: professional-code-review
version: v1
description: Professional code review workflow for Agent engineering projects. Use when Codex is asked to review code, inspect changes before commit, assess bugs, evaluate architecture quality, check tests/evals, review LangGraph/LangChain/RAG/MCP/Skills integrations, or provide release-readiness feedback without immediately modifying code.
---

# Professional Code Review

## Overview

Use this skill to produce rigorous, evidence-based code reviews for this Agent engineering project. Default to review-only behavior: inspect, evaluate, and report findings; do not modify files unless the user explicitly asks for fixes.

## Review workflow

1. Identify the review scope.
   - Inspect `git status --short`.
   - Inspect relevant diffs with `git diff` and, when needed, staged diffs with `git diff --cached`.
   - Separate current-stage changes from unrelated user changes.

2. Understand the intended behavior.
   - Read nearby tests, docs, version notes, and current learning state when they explain the change.
   - For Agent features, trace the request path through router, tools, graph nodes, state, metadata, tests, and eval cases.

3. Review by risk area.
   - Correctness: control flow, state transitions, edge cases, failure paths, data shape consistency.
   - Agent behavior: routing, tool selection, bounded loops, recovery behavior, trace clarity, deterministic fallback.
   - Framework boundaries: LangGraph state/node/edge design, LangChain tool adapter contracts, RAG grounding, MCP boundaries, Skills execution boundaries.
   - Safety: workspace path confinement, secrets handling, destructive operations, network/API-key assumptions.
   - Maintainability: small functions, explicit names, duplicated logic, testability, versioned docs.
   - Tests/evals: unit tests for code behavior, evals for user-visible Agent behavior, failure cases, regression coverage.

4. Verify proportionally.
   - Prefer targeted tests first for the changed area.
   - Run broader tests when the change affects routing, graph state, tool execution, metadata, or eval behavior.
   - For this project, common commands are:
     - `python -m unittest tests.test_langgraph_workflow tests.test_agent tests.test_evals -v`
     - `python -m unittest discover -s tests -v`
     - `python -m cli.eval_runner`

5. Report findings clearly.
   - List findings first, ordered by severity.
   - Include file and line references where possible.
   - Explain impact and the minimal safe fix.
   - If no material issues are found, say so and list residual risks or verification gaps.

## Severity guide

- Critical: data loss, unsafe file access, secret exposure, destructive behavior, broken main execution path.
- High: incorrect Agent routing, broken graph/tool/skill state, failing tests, invalid eval behavior, uncaught failure path.
- Medium: missing edge-case coverage, unclear trace metadata, brittle parsing, duplicated logic that will block near-term iteration.
- Low: naming, formatting, documentation precision, minor test readability.

## Project-specific review rules

- Preserve the staged learning workflow: new stage code should remain uncommitted until the user asks to commit.
- Version files belong under `versions/` and should use Chinese explanations.
- Exercise files belong under `docs/` and must include the stage version in the filename.
- Runtime code identifiers and user-visible strings should stay English unless the user explicitly requests otherwise.
- Code comments may be Chinese when they improve learning.
- Do not include `.vscode/` in commits.
- Do not treat generated caches such as `__pycache__/` as review targets unless they are accidentally tracked.

## Output format

Use this structure:

```text
Findings
- [Severity] path:line — issue
  Impact: ...
  Suggested fix: ...

Verification
- Commands run: ...
- Result: ...

Residual risks
- ...
```

If there are no findings:

```text
Findings
- No material issues found.

Verification
- Commands run: ...
- Result: ...

Residual risks
- ...
```
