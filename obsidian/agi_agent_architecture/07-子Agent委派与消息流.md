# 子 Agent 委派与消息流

## 结论

当前项目的 subagent 还不是完全异步的多 Agent runtime，但已经具备了专业 runtime foundation：角色定义、任务契约、委派记录、交接记录、返回记录、消息信封、上下文边界和状态迁移。

## 结构模型图

```mermaid
classDiagram
    class SubagentSpec {
      +name
      +responsibility
      +handoff_rule
      +input_boundary
      +output_boundary
    }
    class SubagentTaskContract {
      +role_name
      +objective
      +required_inputs
      +expected_outputs
      +recovery_handoff
    }
    class SubagentDelegationRecord {
      +delegation_id
      +parent_objective
      +status
      +child_task
      +order
    }
    class SubagentHandoffRecord {
      +handoff_id
      +from_role
      +to_role
      +reason
      +status
    }
    class SubagentReturnRecord {
      +return_id
      +role_name
      +status
      +returned_outputs
      +next_handoff
    }
    class SubagentMessageEnvelope {
      +message_id
      +session_id
      +from_role
      +to_role
      +message_type
      +status
      +order
    }
    class SubagentContextBoundary {
      +session_id
      +parent_role
      +active_role
      +objective
    }
    class SubagentStateTransition {
      +transition_id
      +from_state
      +to_state
      +actor
      +order
    }

    SubagentDelegationRecord --> SubagentSpec
    SubagentDelegationRecord --> SubagentTaskContract
```

## 委派时序

```mermaid
sequenceDiagram
    participant Parent as Parent Agent
    participant Planner as build_collaboration_plan
    participant Runtime as execute_collaboration_plan
    participant Child as Teacher/Coding Agent Role
    participant Events as runtime metadata

    Parent->>Planner: plan_subagent_collaboration(task)
    Planner-->>Parent: delegation plan + contracts
    Parent->>Runtime: execute_subagent_collaboration(task)
    Runtime->>Child: delegated child task
    Child-->>Runtime: outputs / status / verification
    Runtime-->>Parent: subagent_runtime + delegation metadata
    Parent->>Events: emit delegation / runtime events
```

## 工程判断

- `subagent/team.py` 的重点不是“真的调起第二个模型”，而是先把 runtime contract 设计清楚。
- 这对后续做异步队列、人工审批、消息总线、多 Agent 状态恢复非常关键。

## 关键代码

- [subagent/team.py](../../subagent/team.py)
- [agent/tools.py](../../agent/tools.py)
- [agent/events.py](../../agent/events.py)
