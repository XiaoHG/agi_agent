# State Workflow Flow

本文件用于复盘当前 v2 阶段的工作流执行路径。

## 主流程

```text
User input
  -> WorkspaceAgent.run()
     -> route_intent()
        -> action == "workflow" ?
           -> yes:
              -> build_workflow_plan()
              -> AgentState(...)
              -> WorkspaceAgent._run_workflow()
                 -> execute step 1
                 -> execute step 2
                 -> build_workflow_summary()
              -> return AgentRun
           -> no:
              -> use the existing single-step path
              -> return AgentRun
```

## 成功路径

```text
Read README.md and then count lines.
  -> route: workflow
  -> plan:
     1. read_file README.md
     2. count_lines README.md
  -> state records each completed step
  -> final answer summarizes all tool results
```

## 失败路径

```text
Read not-exist.md and then count lines.
  -> route: workflow
  -> plan:
     1. read_file not-exist.md
     2. count_lines not-exist.md
  -> read_file fails
  -> workflow stops immediately
  -> count_lines is not executed
  -> final answer explains the failure reason
```
