"""Subagent collaboration helpers for the Agent learning workspace."""

from .team import (
    CollaborationPlan,
    SubagentDelegationRecord,
    SubagentSpec,
    SubagentTaskContract,
    build_collaboration_plan,
    build_delegation_record,
    build_subagent_task_contract,
    describe_subagents,
)

__all__ = [
    "CollaborationPlan",
    "SubagentDelegationRecord",
    "SubagentSpec",
    "SubagentTaskContract",
    "build_collaboration_plan",
    "build_delegation_record",
    "build_subagent_task_contract",
    "describe_subagents",
]
