"""Subagent collaboration helpers for the Agent learning workspace."""

from .team import (
    CollaborationPlan,
    SubagentExecutionRecord,
    SubagentDelegationRecord,
    SubagentHandoffRecord,
    SubagentSpec,
    SubagentTaskContract,
    SubagentReturnRecord,
    build_collaboration_plan,
    build_delegation_record,
    build_execution_record,
    build_handoff_record,
    build_subagent_task_contract,
    build_return_record,
    describe_subagents,
    execute_collaboration_plan,
)

__all__ = [
    "CollaborationPlan",
    "SubagentExecutionRecord",
    "SubagentDelegationRecord",
    "SubagentHandoffRecord",
    "SubagentSpec",
    "SubagentTaskContract",
    "SubagentReturnRecord",
    "build_collaboration_plan",
    "build_delegation_record",
    "build_execution_record",
    "build_handoff_record",
    "build_subagent_task_contract",
    "build_return_record",
    "describe_subagents",
    "execute_collaboration_plan",
]
