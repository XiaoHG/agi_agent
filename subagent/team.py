"""Deterministic subagent planning for learning multi-agent boundaries.

This module is the project's subagent runtime design notebook in code form.
It does not try to be a full autonomous multi-agent system yet. Instead, it
models the minimum set of entities needed to learn and reason about:

- who the subagents are
- what each subagent is allowed to do
- how work is handed off
- what evidence is produced on return
- how a collaboration session moves through states

The file is intentionally deterministic so the relationships are easy to read,
test, and later evolve into a richer async runtime.

Mind map:

```mermaid
mindmap
  root((subagent/team.py))
    SubagentSpec
      responsibility
      handoff_rule
      input_boundary
      output_boundary
    SubagentTaskContract
      objective
      required_inputs
      expected_outputs
      recovery_handoff
    SubagentDelegationRecord
      role
      contract
      status
      child_task
    SubagentHandoffRecord
      from_role
      to_role
      reason
      payload_summary
    SubagentReturnRecord
      returned_outputs
      summary
      next_handoff
    SubagentExecutionRecord
      produced_outputs
      verification_note
      recovery_action
    SubagentMessageEnvelope
      message_type
      referenced_records
      status
    SubagentContextBoundary
      allowed_inputs
      blocked_inputs
      expected_outputs
    SubagentStateTransition
      from_state
      to_state
      actor
    SubagentRuntimeSession
      context_boundary
      messages
      transitions
      queue_items
      inbox_entries
      outbox_entries
      claim_records
      approval_requests
      approval_decisions
      task_lifecycle
      watchdog_signals
    CollaborationPlan
      assigned_roles
      contracts
      delegations
      handoffs
      returns
      executions
      runtime_session
      task_lifecycle
      watchdog_signals
```

Reading order:

1. Start with `SubagentSpec` and `SubagentTaskContract`.
2. Then read the evidence records: delegation, handoff, return, execution.
3. Then read `SubagentRuntimeSession` to see how a collaboration flow is
   captured over time.
4. Finally read `CollaborationPlan`, `build_collaboration_plan()`, and
   `execute_collaboration_plan()` to understand the full lifecycle.

Execution flow:

1. 用户输入需求
2. `build_collaboration_plan()` 生成 `CollaborationPlan`
   - 由 `SubagentSpec` 挑选参与角色
   - 由 `build_subagent_task_contract()` 生成任务契约
   - 由 `build_delegation_record()` 生成派工记录
3. `execute_collaboration_plan()` 模拟执行
   - 为每张派工单生成执行记录
   - 生成成果回执
   - 生成角色交接单据
4. `build_runtime_session()` 把这些记录整理成通信信封和状态变更流水
5. 最终把 `runtime_session` 挂载进 `CollaborationPlan`

Plan structure:

- `assigned_roles` -> `SubagentSpec`
- `contracts` -> `SubagentTaskContract`
- `delegations` -> `SubagentDelegationRecord`
- `executions` -> `SubagentExecutionRecord`
- `returns` -> `SubagentReturnRecord`
- `handoffs` -> `SubagentHandoffRecord`
- `runtime_session` -> `SubagentRuntimeSession`
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubagentSpec:
    """Role definition for one project subagent.

    A ``SubagentSpec`` answers the question "what is this role?".
    It defines the role identity and the high-level boundary for when the
    parent flow should hand work to this role.
    """

    name: str               # 子 Agent 的角色名
    responsibility: str     # 该角色负责的核心职责
    handoff_rule: str       # 什么时候切换给它
    input_boundary: str     # 它允许接收的输入边界
    output_boundary: str    # 它必须产出的输出边界

    def to_dict(self) -> dict[str, Any]:
        """Render the role definition as JSON-ready data.

        Returns:
            A plain dictionary that can be stored in traces, checkpoints, or
            JSON reports without depending on dataclass serialization.
        """

        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "handoff_rule": self.handoff_rule,
            "input_boundary": self.input_boundary,
            "output_boundary": self.output_boundary,
        }


@dataclass(frozen=True)
class SubagentTaskContract:
    """Input/output contract for a delegated subtask.

    A ``SubagentTaskContract`` answers the question "what exactly is the child
    role supposed to consume and produce?".

    This is the strongest boundary in the module because it keeps delegation
    bounded: the parent gives a contract, the child returns evidence, and the
    recovery path is explicit when the contract is incomplete or the request is
    ambiguous.
    """

    role_name: str                      # 该子任务分配给哪个角色
    objective: str                      # 该子任务的明确目标
    input_boundary: str                 # 该子任务可消费的信息边界
    required_inputs: tuple[str, ...]    # 完成子任务所需的最小输入
    output_boundary: str                # 该子任务输出的责任边界
    expected_outputs: tuple[str, ...]   # 该子任务预期交付物
    recovery_handoff: str               # 失败或不明确时如何交接恢复

    def to_dict(self) -> dict[str, Any]:
        """Render the contract as JSON-ready data.

        Returns:
            A stable dictionary with tuple fields converted to lists so the
            object remains JSON-friendly.
        """

        return {
            "role_name": self.role_name,
            "objective": self.objective,
            "input_boundary": self.input_boundary,
            "required_inputs": list(self.required_inputs),
            "output_boundary": self.output_boundary,
            "expected_outputs": list(self.expected_outputs),
            "recovery_handoff": self.recovery_handoff,
        }

    def to_text(self) -> str:
        """Render the contract as a compact readable block.

        This form is useful in traces and teaching notes because it puts the
        role target, constraints, and recovery rule in one screen-sized block.
        """

        lines = [
            f"- Role: {self.role_name}",
            f"  Objective: {self.objective}",
            f"  Input boundary: {self.input_boundary}",
            f"  Required inputs: {', '.join(self.required_inputs) if self.required_inputs else 'none'}",
            f"  Output boundary: {self.output_boundary}",
            f"  Expected outputs: {', '.join(self.expected_outputs) if self.expected_outputs else 'none'}",
            f"  Recovery handoff: {self.recovery_handoff}",
        ]
        return "\n".join(lines)


@dataclass(frozen=True)
class SubagentDelegationRecord:
    """Structured record for one delegated child task.

    A delegation record ties a parent objective to one concrete child task.
    It is the "work order" that the parent uses when sending work to a role.
    """

    delegation_id: str              # 本次委派记录的唯一标识
    parent_objective: str           # 上层主任务目标
    role: SubagentSpec              # 被委派的子 Agent 角色
    contract: SubagentTaskContract  # 这次委派绑定的任务契约
    status: str                     # 当前委派状态，例如 planned / completed / failed
    child_task: str                 # 实际下发给子 Agent 的任务描述
    order: int                      # 该委派在协作流程中的顺序
    notes: str                      # 额外说明，通常记录恢复或交接提示

    def to_dict(self) -> dict[str, Any]:
        """Render the delegation record as JSON-ready data.

        Returns:
            A nested dictionary that includes both the role and the contract
            used to create the delegation.
        """

        return {
            "delegation_id": self.delegation_id,
            "parent_objective": self.parent_objective,
            "role": self.role.to_dict(),
            "contract": self.contract.to_dict(),
            "status": self.status,
            "child_task": self.child_task,
            "order": self.order,
            "notes": self.notes,
        }

    def to_text(self) -> str:
        """Render the delegation record as a compact readable block.

        The text version is intentionally short because it is usually embedded
        inside broader collaboration summaries.
        """

        return (
            f"- Delegation {self.delegation_id} [{self.status}] -> {self.role.name}\n"
            f"  Child task: {self.child_task}\n"
            f"  Notes: {self.notes}"
        )


@dataclass(frozen=True)
class SubagentHandoffRecord:
    """Structured handoff from one role to another.

    A handoff record captures the moment work ownership changes from one role
    to the next. It is different from a delegation:

    - delegation = parent assigns a child task
    - handoff = one role passes context to the next role
    """

    handoff_id: str                  # 本次交接记录 ID
    from_role: str                   # 从哪个角色交出
    to_role: str                     # 交给哪个角色
    reason: str                      # 为什么发生交接
    payload_summary: str             # 交接内容摘要
    status: str                      # planned / completed

    def to_dict(self) -> dict[str, Any]:
        """Render the handoff as JSON-ready data."""

        return {
            "handoff_id": self.handoff_id,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "reason": self.reason,
            "payload_summary": self.payload_summary,
            "status": self.status,
        }


@dataclass(frozen=True)
class SubagentReturnRecord:
    """Structured return from one subagent back to the parent flow.

    The return record is where the parent learns whether the child completed
    its bounded objective and what the next action should be.
    """

    return_id: str                      # 本次返回记录 ID
    role_name: str                      # 返回结果的角色
    status: str                         # completed / failed / blocked
    returned_outputs: tuple[str, ...]   # 本次返回交付物
    summary: str                        # 返回摘要
    next_handoff: str                   # 下一步应该交给谁

    def to_dict(self) -> dict[str, Any]:
        """Render the return record as JSON-ready data."""

        return {
            "return_id": self.return_id,
            "role_name": self.role_name,
            "status": self.status,
            "returned_outputs": list(self.returned_outputs),
            "summary": self.summary,
            "next_handoff": self.next_handoff,
        }


@dataclass(frozen=True)
class SubagentExecutionRecord:
    """Execution evidence for one delegated subtask.

    This is the proof object for a delegation. It records what the child
    actually produced and whether that output was considered successful.
    """

    delegation_id: str                  # 对应的委派 ID
    role_name: str                      # 执行角色名
    status: str                         # completed / failed / blocked
    child_task: str                     # 实际执行的子任务
    produced_outputs: tuple[str, ...]   # 实际产出
    verification_note: str              # 验证或失败说明
    recovery_action: str                # 失败时的恢复动作

    def to_dict(self) -> dict[str, Any]:
        """Render the execution record as JSON-ready data."""

        return {
            "delegation_id": self.delegation_id,
            "role_name": self.role_name,
            "status": self.status,
            "child_task": self.child_task,
            "produced_outputs": list(self.produced_outputs),
            "verification_note": self.verification_note,
            "recovery_action": self.recovery_action,
        }


@dataclass(frozen=True)
class SubagentMessageEnvelope:
    """Structured message exchanged inside one subagent runtime session.

    This is the message-level counterpart to delegation and return records.
    It allows the runtime to keep a stable, ordered communication trail.
    """

    message_id: str                     # 本次消息的唯一标识
    session_id: str                     # 所属 runtime session
    from_role: str                      # 消息发送方
    to_role: str                        # 消息接收方
    message_type: str                   # delegation / handoff / return / recovery
    summary: str                        # 消息摘要
    referenced_records: tuple[str, ...] # 关联的 delegation / handoff / return 记录
    status: str                         # emitted / consumed / blocked
    order: int                          # 在 session 中的顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the message envelope as JSON-ready data."""

        return {
            "message_id": self.message_id,
            "session_id": self.session_id,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "message_type": self.message_type,
            "summary": self.summary,
            "referenced_records": list(self.referenced_records),
            "status": self.status,
            "order": self.order,
        }


@dataclass(frozen=True)
class SubagentContextBoundary:
    """Runtime context boundary for the active delegated scope.

    This record answers: "what can the active child see, what is blocked, and
    what outputs are expected before control returns to the parent?"
    """

    session_id: str                     # 所属 runtime session
    parent_role: str                    # 上层父角色
    active_role: str                    # 当前激活的子角色
    objective: str                      # 当前会话目标
    allowed_inputs: tuple[str, ...]     # 允许进入该上下文的输入
    blocked_inputs: tuple[str, ...]     # 明确不允许进入该上下文的信息
    expected_outputs: tuple[str, ...]   # 该上下文预期产出

    def to_dict(self) -> dict[str, Any]:
        """Render the context boundary as JSON-ready data."""

        return {
            "session_id": self.session_id,
            "parent_role": self.parent_role,
            "active_role": self.active_role,
            "objective": self.objective,
            "allowed_inputs": list(self.allowed_inputs),
            "blocked_inputs": list(self.blocked_inputs),
            "expected_outputs": list(self.expected_outputs),
        }


@dataclass(frozen=True)
class SubagentStateTransition:
    """One runtime state transition inside a subagent session.

    State transitions make the collaboration flow observable. Without them the
    session would only show static records, not movement across states.
    """

    transition_id: str    # 状态迁移 ID
    session_id: str       # 所属 runtime session
    from_state: str       # 迁移前状态
    to_state: str         # 迁移后状态
    actor: str            # 触发本次状态变化的角色
    reason: str           # 状态变化原因
    order: int            # 在 session 中的顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the state transition as JSON-ready data."""

        return {
            "transition_id": self.transition_id,
            "session_id": self.session_id,
            "from_state": self.from_state,
            "to_state": self.to_state,
            "actor": self.actor,
            "reason": self.reason,
            "order": self.order,
        }


@dataclass(frozen=True)
class SubagentQueueItem:
    """One queued delegation task inside the async-ready collaboration runtime."""

    queue_item_id: str     # 队列任务 ID
    session_id: str        # 所属 runtime session
    delegation_id: str     # 对应的 delegation 记录
    from_role: str         # 任务由哪个角色发出
    to_role: str           # 任务发给哪个子 Agent
    status: str            # pending / running / blocked / completed / failed
    summary: str           # 队列任务摘要
    order: int             # 队列中的顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the queue item as JSON-ready data."""

        return {
            "queue_item_id": self.queue_item_id,
            "session_id": self.session_id,
            "delegation_id": self.delegation_id,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "status": self.status,
            "summary": self.summary,
            "order": self.order,
        }


@dataclass(frozen=True)
class SubagentInboxEntry:
    """One inbox entry visible to a target subagent."""

    inbox_entry_id: str    # inbox 记录 ID
    session_id: str        # 所属 runtime session
    role_name: str         # 收件 Agent 角色
    queue_item_id: str     # 对应队列任务 ID
    delegation_id: str     # 对应 delegation 记录
    status: str            # pending / running / blocked / completed / failed
    summary: str           # inbox 任务摘要
    order: int             # inbox 中的顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the inbox entry as JSON-ready data."""

        return {
            "inbox_entry_id": self.inbox_entry_id,
            "session_id": self.session_id,
            "role_name": self.role_name,
            "queue_item_id": self.queue_item_id,
            "delegation_id": self.delegation_id,
            "status": self.status,
            "summary": self.summary,
            "order": self.order,
        }


@dataclass(frozen=True)
class SubagentOutboxEntry:
    """One outbound status/result message emitted by a subagent."""

    outbox_entry_id: str   # outbox 记录 ID
    session_id: str        # 所属 runtime session
    role_name: str         # 发件 Agent 角色
    delegation_id: str     # 对应 delegation 记录
    destination_role: str  # 发给谁
    status: str            # emitted / completed / failed / blocked
    summary: str           # outbox 摘要
    order: int             # outbox 中的顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the outbox entry as JSON-ready data."""

        return {
            "outbox_entry_id": self.outbox_entry_id,
            "session_id": self.session_id,
            "role_name": self.role_name,
            "delegation_id": self.delegation_id,
            "destination_role": self.destination_role,
            "status": self.status,
            "summary": self.summary,
            "order": self.order,
        }


@dataclass(frozen=True)
class SubagentClaimRecord:
    """Structured evidence that a queued task was claimed by one role."""

    claim_id: str          # claim 记录 ID
    session_id: str        # 所属 runtime session
    queue_item_id: str     # 被认领的队列任务 ID
    delegation_id: str     # 对应 delegation 记录
    role_name: str         # 认领该任务的角色
    status: str            # claimed / completed / failed / blocked
    note: str              # claim 说明
    order: int             # claim 顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the claim record as JSON-ready data."""

        return {
            "claim_id": self.claim_id,
            "session_id": self.session_id,
            "queue_item_id": self.queue_item_id,
            "delegation_id": self.delegation_id,
            "role_name": self.role_name,
            "status": self.status,
            "note": self.note,
            "order": self.order,
        }


@dataclass(frozen=True)
class RiskClassification:
    """Deterministic risk classification for one collaboration objective."""

    risk_level: str                     # low / medium / high
    reasons: tuple[str, ...]            # 风险判定原因
    requires_approval: bool             # 是否需要审批
    blocked_actions: tuple[str, ...]    # 被阻断的高风险动作

    def to_dict(self) -> dict[str, Any]:
        """Render the risk classification as JSON-ready data."""

        return {
            "risk_level": self.risk_level,
            "reasons": list(self.reasons),
            "requires_approval": self.requires_approval,
            "blocked_actions": list(self.blocked_actions),
        }


@dataclass(frozen=True)
class ApprovalRequest:
    """Structured request asking whether a risky collaboration can proceed."""

    request_id: str             # 审批请求 ID
    session_id: str             # 所属 runtime session
    requester_role: str         # 发起审批请求的角色
    target_role: str            # 需要被保护的执行角色
    requested_action: str       # 请求审批的动作描述
    objective: str              # 关联的总目标
    risk: RiskClassification    # 风险分类结果
    status: str                 # requested / approved / rejected / revise_required

    def to_dict(self) -> dict[str, Any]:
        """Render the approval request as JSON-ready data."""

        return {
            "request_id": self.request_id,
            "session_id": self.session_id,
            "requester_role": self.requester_role,
            "target_role": self.target_role,
            "requested_action": self.requested_action,
            "objective": self.objective,
            "risk": self.risk.to_dict(),
            "status": self.status,
        }


@dataclass(frozen=True)
class ApprovalDecision:
    """Structured approval outcome for one risky collaboration step."""

    decision_id: str            # 审批决策 ID
    request_id: str             # 对应审批请求 ID
    reviewer_role: str          # 审批者角色
    decision: str               # approved / rejected / revise_required
    rationale: str              # 审批理由
    next_action: str            # 下一步动作

    def to_dict(self) -> dict[str, Any]:
        """Render the approval decision as JSON-ready data."""

        return {
            "decision_id": self.decision_id,
            "request_id": self.request_id,
            "reviewer_role": self.reviewer_role,
            "decision": self.decision,
            "rationale": self.rationale,
            "next_action": self.next_action,
        }


@dataclass(frozen=True)
class GuardedHandoffRecord:
    """A handoff that is only allowed after approval has been checked."""

    guarded_handoff_id: str    # 受保护交接 ID
    from_role: str             # 交出角色
    to_role: str               # 接收角色
    approval_status: str       # approved / rejected / revise_required
    risk_level: str            # 这次交接的风险级别
    reason: str                # 为什么发生交接
    payload_summary: str       # 交接内容摘要
    fallback_action: str       # 审批未通过时的回退动作

    def to_dict(self) -> dict[str, Any]:
        """Render the guarded handoff as JSON-ready data."""

        return {
            "guarded_handoff_id": self.guarded_handoff_id,
            "from_role": self.from_role,
            "to_role": self.to_role,
            "approval_status": self.approval_status,
            "risk_level": self.risk_level,
            "reason": self.reason,
            "payload_summary": self.payload_summary,
            "fallback_action": self.fallback_action,
        }


@dataclass(frozen=True)
class TaskMilestoneRecord:
    """A named checkpoint inside one long-horizon task."""

    milestone_id: str           # milestone 记录 ID
    session_id: str             # 所属 runtime session
    title: str                  # 里程碑标题
    status: str                 # planned / reached / blocked / paused / expired / abandoned / completed
    evidence_summary: str       # 支撑该里程碑状态的摘要
    order: int                  # 里程碑顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the milestone as JSON-ready data."""

        return {
            "milestone_id": self.milestone_id,
            "session_id": self.session_id,
            "title": self.title,
            "status": self.status,
            "evidence_summary": self.evidence_summary,
            "order": self.order,
        }


@dataclass(frozen=True)
class TaskWatchdogSignal:
    """A health signal used to keep long-horizon tasks observable."""

    signal_id: str              # watchdog 信号 ID
    session_id: str             # 所属 runtime session
    signal_type: str            # healthy / stalled / paused / expired / abandoned
    severity: str               # low / medium / high
    summary: str                # 信号摘要
    recommended_action: str     # 推荐动作
    order: int                  # 信号顺序

    def to_dict(self) -> dict[str, Any]:
        """Render the watchdog signal as JSON-ready data."""

        return {
            "signal_id": self.signal_id,
            "session_id": self.session_id,
            "signal_type": self.signal_type,
            "severity": self.severity,
            "summary": self.summary,
            "recommended_action": self.recommended_action,
            "order": self.order,
        }


@dataclass(frozen=True)
class TaskLifecycleRecord:
    """Structured lifecycle evidence for one long-horizon task."""

    lifecycle_id: str                 # 生命周期记录 ID
    session_id: str                   # 所属 runtime session
    objective: str                    # 关联的长期任务目标
    state: str                        # created / running / paused / resumed / expired / abandoned / blocked / failed / completed
    health: str                       # healthy / paused / stalled / expired / abandoned / blocked / failed
    progress_stage: str               # 当前进展阶段
    current_milestone: str            # 当前聚焦的里程碑
    paused_reason: str                # 暂停原因
    resume_hint: str                  # 恢复提示
    terminal_reason: str              # 结束原因
    next_safe_action: str             # 下一步安全动作
    milestones: tuple[TaskMilestoneRecord, ...]  # 里程碑记录

    def to_dict(self) -> dict[str, Any]:
        """Render the lifecycle record as JSON-ready data."""

        return {
            "lifecycle_id": self.lifecycle_id,
            "session_id": self.session_id,
            "objective": self.objective,
            "state": self.state,
            "health": self.health,
            "progress_stage": self.progress_stage,
            "current_milestone": self.current_milestone,
            "paused_reason": self.paused_reason,
            "resume_hint": self.resume_hint,
            "terminal_reason": self.terminal_reason,
            "next_safe_action": self.next_safe_action,
            "milestones": [milestone.to_dict() for milestone in self.milestones],
        }


@dataclass(frozen=True)
class SubagentRuntimeSession:
    """Execution-layer runtime session for one collaboration flow.

    This is the most complete evidence object in the module. It binds together
    the collaboration plan, context boundary, messages, and state transitions
    into one executable history record.
    """

    session_id: str                                  # runtime session 唯一标识
    objective: str                                   # 本次会话的总目标
    parent_role: str                                 # 发起该会话的父角色
    child_roles: tuple[str, ...]                     # 本次会话涉及的子角色
    active_role: str                                 # 当前活跃角色
    current_delegation_id: str                       # 当前处理的 delegation
    execution_mode: str                              # deterministic / async-ready
    status: str                                      # created / running / completed / failed
    terminal_reason: str                             # 结束原因
    context_boundary: SubagentContextBoundary        # 当前上下文边界
    messages: tuple[SubagentMessageEnvelope, ...]    # 会话中的消息封装
    transitions: tuple[SubagentStateTransition, ...] # 会话状态迁移
    queue_items: tuple[SubagentQueueItem, ...]       # async delegation queue 快照
    inbox_entries: tuple[SubagentInboxEntry, ...]    # 各子 Agent inbox 快照
    outbox_entries: tuple[SubagentOutboxEntry, ...]  # 各子 Agent outbox 快照
    claim_records: tuple[SubagentClaimRecord, ...]   # task claim / complete / fail 记录
    guarded_handoffs: tuple[GuardedHandoffRecord, ...]  # 经审批保护的交接记录
    approval_requests: tuple[ApprovalRequest, ...]   # 审批请求记录
    approval_decisions: tuple[ApprovalDecision, ...] # 审批决策记录
    task_lifecycle: TaskLifecycleRecord | None       # 长任务生命周期记录
    watchdog_signals: tuple[TaskWatchdogSignal, ...]  # 长任务健康信号

    def to_dict(self) -> dict[str, Any]:
        """Render the runtime session as JSON-ready data."""

        return {
            "session_id": self.session_id,
            "objective": self.objective,
            "parent_role": self.parent_role,
            "child_roles": list(self.child_roles),
            "active_role": self.active_role,
            "current_delegation_id": self.current_delegation_id,
            "execution_mode": self.execution_mode,
            "status": self.status,
            "terminal_reason": self.terminal_reason,
            "context_boundary": self.context_boundary.to_dict(),
            "messages": [message.to_dict() for message in self.messages],
            "transitions": [transition.to_dict() for transition in self.transitions],
            "queue_items": [item.to_dict() for item in self.queue_items],
            "inbox_entries": [entry.to_dict() for entry in self.inbox_entries],
            "outbox_entries": [entry.to_dict() for entry in self.outbox_entries],
            "claim_records": [record.to_dict() for record in self.claim_records],
            "guarded_handoffs": [handoff.to_dict() for handoff in self.guarded_handoffs],
            "approval_requests": [request.to_dict() for request in self.approval_requests],
            "approval_decisions": [decision.to_dict() for decision in self.approval_decisions],
            "task_lifecycle": None if self.task_lifecycle is None else self.task_lifecycle.to_dict(),
            "watchdog_signals": [signal.to_dict() for signal in self.watchdog_signals],
        }


@dataclass(frozen=True)
class CollaborationPlan:
    """A small ordered plan that assigns work to subagents.

    ``CollaborationPlan`` is the parent-facing orchestration object. It says:

    - which roles are involved
    - what contracts they receive
    - how the work is delegated
    - how the roles hand off to each other
    - what evidence came back
    - whether the whole flow succeeded or failed
    """

    objective: str                                          # 当前协作要完成的总目标
    assigned_roles: tuple[SubagentSpec, ...]                # 参与本次协作的角色集合
    contracts: tuple[SubagentTaskContract, ...]             # 各角色对应的任务契约
    delegations: tuple[SubagentDelegationRecord, ...]       # 结构化子任务委派记录
    steps: tuple[str, ...]                                  # 面向展示的协作步骤说明
    handoffs: tuple[SubagentHandoffRecord, ...] = ()        # 角色之间的交接记录
    guarded_handoffs: tuple[GuardedHandoffRecord, ...] = () # 经审批保护的交接记录
    returns: tuple[SubagentReturnRecord, ...] = ()          # 子任务回传记录
    executions: tuple[SubagentExecutionRecord, ...] = ()    # 子任务执行轨迹
    risk: RiskClassification | None = None                  # 当前协作风险分类
    approval_request: ApprovalRequest | None = None         # 当前协作审批请求
    approval_decision: ApprovalDecision | None = None       # 当前协作审批决策
    task_lifecycle: TaskLifecycleRecord | None = None       # 当前协作生命周期记录
    watchdog_signals: tuple[TaskWatchdogSignal, ...] = ()   # 当前协作健康信号
    status: str = "planned"                                 # planned / completed / failed
    recovery_handoff: str = ""                              # 整体失败时的恢复动作
    runtime_session: SubagentRuntimeSession | None = None   # 多 Agent runtime session

    def to_dict(self) -> dict[str, Any]:
        """Render the collaboration plan as JSON-ready data."""

        return {
            "objective": self.objective,
            "assigned_roles": [role.to_dict() for role in self.assigned_roles],
            "contracts": [contract.to_dict() for contract in self.contracts],
            "delegations": [delegation.to_dict() for delegation in self.delegations],
            "steps": list(self.steps),
            "handoffs": [handoff.to_dict() for handoff in self.handoffs],
            "guarded_handoffs": [handoff.to_dict() for handoff in self.guarded_handoffs],
            "returns": [item.to_dict() for item in self.returns],
            "executions": [execution.to_dict() for execution in self.executions],
            "risk": None if self.risk is None else self.risk.to_dict(),
            "approval_request": None if self.approval_request is None else self.approval_request.to_dict(),
            "approval_decision": None if self.approval_decision is None else self.approval_decision.to_dict(),
            "task_lifecycle": None if self.task_lifecycle is None else self.task_lifecycle.to_dict(),
            "watchdog_signals": [signal.to_dict() for signal in self.watchdog_signals],
            "status": self.status,
            "recovery_handoff": self.recovery_handoff,
            "runtime_session": None if self.runtime_session is None else self.runtime_session.to_dict(),
        }

    def to_text(self) -> str:
        """Render the collaboration plan as a readable learning summary.

        The text version is intentionally verbose because it is designed for
        learners who want to see the full collaboration story in one place.
        """

        lines = [f"Collaboration objective: {self.objective}", "Assigned roles:"]
        for role in self.assigned_roles:
            lines.append(f"- {role.name}: {role.responsibility}")
            lines.append(f"  Input boundary: {role.input_boundary}")
            lines.append(f"  Output boundary: {role.output_boundary}")
        lines.append("Contracts:")
        for contract in self.contracts:
            lines.append(contract.to_text())
        lines.append("Delegations:")
        for delegation in self.delegations:
            lines.append(delegation.to_text())
        if self.handoffs:
            lines.append("Handoffs:")
            for handoff in self.handoffs:
                lines.append(
                    f"- {handoff.handoff_id} [{handoff.status}] {handoff.from_role} -> {handoff.to_role}: {handoff.reason}"
                )
        if self.guarded_handoffs:
            lines.append("Guarded handoffs:")
            for handoff in self.guarded_handoffs:
                lines.append(
                    f"- {handoff.guarded_handoff_id} [{handoff.approval_status}] {handoff.from_role} -> {handoff.to_role}: "
                    f"{handoff.reason} (risk={handoff.risk_level})"
                )
        if self.executions:
            lines.append("Executions:")
            for execution in self.executions:
                lines.append(
                    f"- {execution.delegation_id} [{execution.status}] {execution.role_name}: {execution.verification_note}"
                )
        if self.risk is not None:
            lines.append("Risk classification:")
            lines.append(f"- level={self.risk.risk_level} requires_approval={self.risk.requires_approval}")
        if self.approval_request is not None:
            lines.append("Approval request:")
            lines.append(
                f"- {self.approval_request.request_id} [{self.approval_request.status}] "
                f"{self.approval_request.requester_role} -> {self.approval_request.target_role}"
            )
        if self.approval_decision is not None:
            lines.append("Approval decision:")
            lines.append(
                f"- {self.approval_decision.decision_id} [{self.approval_decision.decision}] "
                f"{self.approval_decision.reviewer_role}: {self.approval_decision.rationale}"
            )
        if self.task_lifecycle is not None:
            lines.append("Task lifecycle:")
            lines.append(
                f"- {self.task_lifecycle.lifecycle_id} [{self.task_lifecycle.state}] "
                f"health={self.task_lifecycle.health} milestone={self.task_lifecycle.current_milestone}"
            )
            lines.append(f"  Next safe action: {self.task_lifecycle.next_safe_action}")
            if self.task_lifecycle.paused_reason:
                lines.append(f"  Paused reason: {self.task_lifecycle.paused_reason}")
            if self.task_lifecycle.resume_hint:
                lines.append(f"  Resume hint: {self.task_lifecycle.resume_hint}")
        if self.watchdog_signals:
            lines.append("Watchdog signals:")
            for signal in self.watchdog_signals:
                lines.append(
                    f"- {signal.signal_id} [{signal.signal_type}/{signal.severity}] {signal.summary}"
                )
        if self.returns:
            lines.append("Returns:")
            for item in self.returns:
                lines.append(
                    f"- {item.return_id} [{item.status}] {item.role_name}: {item.summary} -> next {item.next_handoff}"
                )
        if self.runtime_session is not None:
            lines.append("Runtime session:")
            lines.append(
                f"- {self.runtime_session.session_id} [{self.runtime_session.status}] "
                f"mode={self.runtime_session.execution_mode} active={self.runtime_session.active_role}"
            )
            lines.append(
                f"  Context: {self.runtime_session.context_boundary.parent_role} -> "
                f"{self.runtime_session.context_boundary.active_role}"
            )
            lines.append(f"  Messages: {len(self.runtime_session.messages)}")
            lines.append(f"  Transitions: {len(self.runtime_session.transitions)}")
            lines.append(f"  Queue items: {len(self.runtime_session.queue_items)}")
            lines.append(f"  Inbox entries: {len(self.runtime_session.inbox_entries)}")
            lines.append(f"  Outbox entries: {len(self.runtime_session.outbox_entries)}")
            lines.append(f"  Claim records: {len(self.runtime_session.claim_records)}")
            lines.append(f"  Guarded handoffs: {len(self.runtime_session.guarded_handoffs)}")
            lines.append(f"  Approval requests: {len(self.runtime_session.approval_requests)}")
            lines.append(f"  Approval decisions: {len(self.runtime_session.approval_decisions)}")
            lines.append(
                f"  Task lifecycle: {None if self.runtime_session.task_lifecycle is None else self.runtime_session.task_lifecycle.state}"
            )
            lines.append(f"  Watchdog signals: {len(self.runtime_session.watchdog_signals)}")
        lines.append("Workflow:")
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. {step}")
        lines.append(f"Plan status: {self.status}")
        if self.recovery_handoff:
            lines.append(f"Recovery handoff: {self.recovery_handoff}")
        return "\n".join(lines)


def get_default_subagents() -> tuple[SubagentSpec, ...]:
    """Return the default project subagents.

    The current repository intentionally starts with two default roles:

    - ``teacher_agent`` for explanation, planning, and boundary setting
    - ``coding_agent`` for implementation, verification, and bug fixing
    """

    return (
        SubagentSpec(
            name="teacher_agent",
            responsibility="Explain concepts, architecture, code flow, and learning checkpoints.",
            handoff_rule="Use for learning, explanation, review, and planning questions.",
            input_boundary="Consumes problem framing, project context, and expected learning goals.",
            output_boundary="Returns explanation, boundary analysis, and handoff guidance.",
        ),
        SubagentSpec(
            name="coding_agent",
            responsibility="Implement changes, fix bugs, add tests, and verify behavior.",
            handoff_rule="Use for code changes, debugging, tests, and validation.",
            input_boundary="Consumes a bounded implementation request, target files, and test expectations.",
            output_boundary="Returns code changes, test updates, and verification evidence.",
        ),
    )


def build_subagent_task_contract(role: SubagentSpec, objective: str) -> SubagentTaskContract:
    """Build a deterministic contract for one subagent role.

    Args:
        role: The role that will receive the task.
        objective: The parent objective to translate into a bounded contract.

    Returns:
        A role-specific contract that makes the delegation safe and explicit.
    """

    if role.name == "teacher_agent":
        return SubagentTaskContract(
            role_name=role.name,
            objective=f"Clarify the request and define the handoff boundary for: {objective}",
            input_boundary=role.input_boundary,
            required_inputs=("user goal", "project context", "known constraints"),
            output_boundary=role.output_boundary,
            expected_outputs=("concept explanation", "safe handoff rule", "learning checkpoint"),
            recovery_handoff="If implementation becomes necessary, hand off to coding_agent with the smallest safe change.",
        )
    return SubagentTaskContract(
        role_name=role.name,
        objective=f"Implement the bounded change for: {objective}",
        input_boundary=role.input_boundary,
        required_inputs=("teacher summary", "target files", "acceptance criteria", "test expectations"),
        output_boundary=role.output_boundary,
        expected_outputs=("code patch", "test updates", "verification notes"),
        recovery_handoff="If the request is underspecified, return to teacher_agent for clarification before editing files.",
    )


def build_delegation_record(
    parent_objective: str,
    role: SubagentSpec,
    contract: SubagentTaskContract,
    order: int,
) -> SubagentDelegationRecord:
    """Build a deterministic delegation record for a child task.

    The order field is important because it keeps the collaboration flow
    deterministic and easy to replay in traces.
    """

    return SubagentDelegationRecord(
        delegation_id=f"{role.name}-{order:02d}",
        parent_objective=parent_objective,
        role=role,
        contract=contract,
        status="planned",
        child_task=contract.objective,
        order=order,
        notes=contract.recovery_handoff,
    )


def build_handoff_record(
    from_role: str,
    to_role: str,
    reason: str,
    payload_summary: str,
    order: int,
) -> SubagentHandoffRecord:
    """Build a deterministic handoff record between two roles.

    The payload summary should be concise because this record is meant to
    capture just enough context for the next role to continue.
    """

    return SubagentHandoffRecord(
        handoff_id=f"handoff-{order:02d}",
        from_role=from_role,
        to_role=to_role,
        reason=reason,
        payload_summary=payload_summary,
        status="completed",
    )


def build_return_record(
    role_name: str,
    status: str,
    returned_outputs: tuple[str, ...],
    summary: str,
    next_handoff: str,
    order: int,
) -> SubagentReturnRecord:
    """Build a deterministic return record for one role.

    The return record is the parent's inspection point for the child role's
    output. It is where we decide whether the next handoff should happen.
    """

    return SubagentReturnRecord(
        return_id=f"return-{order:02d}",
        role_name=role_name,
        status=status,
        returned_outputs=returned_outputs,
        summary=summary,
        next_handoff=next_handoff,
    )


def build_execution_record(
    delegation: SubagentDelegationRecord,
    *,
    status: str,
    produced_outputs: tuple[str, ...],
    verification_note: str,
    recovery_action: str,
) -> SubagentExecutionRecord:
    """Build a deterministic child-task execution record.

    This record is the proof that a delegated task was actually executed and
    not merely planned.
    """

    return SubagentExecutionRecord(
        delegation_id=delegation.delegation_id,
        role_name=delegation.role.name,
        status=status,
        child_task=delegation.child_task,
        produced_outputs=produced_outputs,
        verification_note=verification_note,
        recovery_action=recovery_action,
    )


def build_message_envelope(
    *,
    session_id: str,
    from_role: str,
    to_role: str,
    message_type: str,
    summary: str,
    referenced_records: tuple[str, ...],
    status: str,
    order: int,
) -> SubagentMessageEnvelope:
    """Build a deterministic runtime message envelope.

    The envelope is intentionally generic so it can represent delegation,
    handoff, return, and recovery messages using the same structure.
    """

    return SubagentMessageEnvelope(
        message_id=f"message-{order:02d}",
        session_id=session_id,
        from_role=from_role,
        to_role=to_role,
        message_type=message_type,
        summary=summary,
        referenced_records=referenced_records,
        status=status,
        order=order,
    )


def build_context_boundary(
    *,
    session_id: str,
    parent_role: str,
    active_role: str,
    objective: str,
    required_inputs: tuple[str, ...],
    expected_outputs: tuple[str, ...],
) -> SubagentContextBoundary:
    """Build a deterministic parent/child context boundary.

    ``blocked_inputs`` is hard-coded here on purpose. It makes the boundary
    visible and avoids accidentally treating a delegated child as if it had
    unrestricted access to the workspace or to parent-only authority.
    """

    return SubagentContextBoundary(
        session_id=session_id,
        parent_role=parent_role,
        active_role=active_role,
        objective=objective,
        allowed_inputs=required_inputs,
        blocked_inputs=(
            "unbounded workspace mutation",
            "implicit role reassignment",
            "outputs outside the delegated contract",
        ),
        expected_outputs=expected_outputs,
    )


def build_state_transition(
    *,
    session_id: str,
    from_state: str,
    to_state: str,
    actor: str,
    reason: str,
    order: int,
) -> SubagentStateTransition:
    """Build a deterministic runtime state transition.

    Each transition is indexed so the final runtime session can be replayed in
    the exact order in which the collaboration progressed.
    """

    return SubagentStateTransition(
        transition_id=f"transition-{order:02d}",
        session_id=session_id,
        from_state=from_state,
        to_state=to_state,
        actor=actor,
        reason=reason,
        order=order,
    )


def build_queue_item(
    *,
    session_id: str,
    delegation: SubagentDelegationRecord,
    from_role: str,
    status: str,
    order: int,
) -> SubagentQueueItem:
    """Build one async-ready delegation queue item."""

    return SubagentQueueItem(
        queue_item_id=f"queue-{order:02d}",
        session_id=session_id,
        delegation_id=delegation.delegation_id,
        from_role=from_role,
        to_role=delegation.role.name,
        status=status,
        summary=delegation.child_task,
        order=order,
    )


def build_inbox_entry(
    *,
    session_id: str,
    role_name: str,
    queue_item_id: str,
    delegation_id: str,
    status: str,
    summary: str,
    order: int,
) -> SubagentInboxEntry:
    """Build one inbox entry for the receiving subagent."""

    return SubagentInboxEntry(
        inbox_entry_id=f"inbox-{order:02d}",
        session_id=session_id,
        role_name=role_name,
        queue_item_id=queue_item_id,
        delegation_id=delegation_id,
        status=status,
        summary=summary,
        order=order,
    )


def build_outbox_entry(
    *,
    session_id: str,
    role_name: str,
    delegation_id: str,
    destination_role: str,
    status: str,
    summary: str,
    order: int,
) -> SubagentOutboxEntry:
    """Build one outbox entry for the sending subagent."""

    return SubagentOutboxEntry(
        outbox_entry_id=f"outbox-{order:02d}",
        session_id=session_id,
        role_name=role_name,
        delegation_id=delegation_id,
        destination_role=destination_role,
        status=status,
        summary=summary,
        order=order,
    )


def build_claim_record(
    *,
    session_id: str,
    queue_item_id: str,
    delegation_id: str,
    role_name: str,
    status: str,
    note: str,
    order: int,
) -> SubagentClaimRecord:
    """Build one task-claim record for the async delegation lifecycle."""

    return SubagentClaimRecord(
        claim_id=f"claim-{order:02d}",
        session_id=session_id,
        queue_item_id=queue_item_id,
        delegation_id=delegation_id,
        role_name=role_name,
        status=status,
        note=note,
        order=order,
    )


def build_risk_classification(user_input: str) -> RiskClassification:
    """Classify the collaboration objective into a deterministic risk tier."""

    lowered = user_input.lower()
    reasons: list[str] = []
    blocked_actions: list[str] = []
    risk_level = "low"

    if any(keyword in lowered for keyword in ("delete", "remove", "overwrite")):
        risk_level = "high"
        reasons.append("The task requests destructive mutation.")
        blocked_actions.append("destructive workspace mutation")
    if any(keyword in lowered for keyword in ("write project file", "mcp write", "write file", "publish", "commit")):
        risk_level = "high"
        reasons.append("The task requests an external or persistent write action.")
        blocked_actions.append("unguarded write operation")
    if any(keyword in lowered for keyword in ("approval", "review", "guarded", "permission")):
        risk_level = "medium" if risk_level == "low" else risk_level
        reasons.append("The task references a gated workflow.")
    if any(keyword in lowered for keyword in ("bug fix", "implement", "test", "code", "refactor")) and risk_level == "low":
        risk_level = "medium"
        reasons.append("The task changes code or behavior but stays within the workspace.")

    if not reasons:
        reasons.append("The task is a bounded learning or explanation request.")

    return RiskClassification(
        risk_level=risk_level,
        reasons=tuple(reasons),
        requires_approval=risk_level == "high",
        blocked_actions=tuple(blocked_actions),
    )


def build_approval_request(
    *,
    session_id: str,
    requester_role: str,
    target_role: str,
    requested_action: str,
    objective: str,
    risk: RiskClassification,
) -> ApprovalRequest:
    """Build one approval request for a risky collaboration step."""

    return ApprovalRequest(
        request_id=f"approval-{session_id}",
        session_id=session_id,
        requester_role=requester_role,
        target_role=target_role,
        requested_action=requested_action,
        objective=objective,
        risk=risk,
        status="requested",
    )


def build_approval_decision(
    *,
    request: ApprovalRequest,
    decision: str,
    rationale: str,
    next_action: str,
) -> ApprovalDecision:
    """Build one approval decision record."""

    return ApprovalDecision(
        decision_id=f"decision-{request.session_id}",
        request_id=request.request_id,
        reviewer_role="teacher_agent",
        decision=decision,
        rationale=rationale,
        next_action=next_action,
    )


def build_guarded_handoff_record(
    *,
    from_role: str,
    to_role: str,
    approval_status: str,
    risk_level: str,
    reason: str,
    payload_summary: str,
    fallback_action: str,
    order: int,
) -> GuardedHandoffRecord:
    """Build one approval-guarded handoff record."""

    return GuardedHandoffRecord(
        guarded_handoff_id=f"guarded-handoff-{order:02d}",
        from_role=from_role,
        to_role=to_role,
        approval_status=approval_status,
        risk_level=risk_level,
        reason=reason,
        payload_summary=payload_summary,
        fallback_action=fallback_action,
    )


def build_task_milestone_record(
    *,
    session_id: str,
    title: str,
    status: str,
    evidence_summary: str,
    order: int,
) -> TaskMilestoneRecord:
    """Build one deterministic long-horizon task milestone record."""

    return TaskMilestoneRecord(
        milestone_id=f"milestone-{order:02d}",
        session_id=session_id,
        title=title,
        status=status,
        evidence_summary=evidence_summary,
        order=order,
    )


def build_task_watchdog_signal(
    *,
    session_id: str,
    signal_type: str,
    severity: str,
    summary: str,
    recommended_action: str,
    order: int,
) -> TaskWatchdogSignal:
    """Build one deterministic watchdog signal for a long-horizon task."""

    return TaskWatchdogSignal(
        signal_id=f"watchdog-{order:02d}",
        session_id=session_id,
        signal_type=signal_type,
        severity=severity,
        summary=summary,
        recommended_action=recommended_action,
        order=order,
    )


def build_task_lifecycle_record(
    *,
    session_id: str,
    objective: str,
    state: str,
    health: str,
    progress_stage: str,
    current_milestone: str,
    paused_reason: str,
    resume_hint: str,
    terminal_reason: str,
    next_safe_action: str,
    milestones: tuple[TaskMilestoneRecord, ...],
) -> TaskLifecycleRecord:
    """Build the task lifecycle record for a long-horizon collaboration."""

    return TaskLifecycleRecord(
        lifecycle_id=f"lifecycle-{session_id}",
        session_id=session_id,
        objective=objective,
        state=state,
        health=health,
        progress_stage=progress_stage,
        current_milestone=current_milestone,
        paused_reason=paused_reason,
        resume_hint=resume_hint,
        terminal_reason=terminal_reason,
        next_safe_action=next_safe_action,
        milestones=milestones,
    )


def build_runtime_session(
    *,
    plan: CollaborationPlan,
    handoffs: tuple[SubagentHandoffRecord, ...],
    guarded_handoffs: tuple[GuardedHandoffRecord, ...],
    returns: tuple[SubagentReturnRecord, ...],
    executions: tuple[SubagentExecutionRecord, ...],
    approval_requests: tuple[ApprovalRequest, ...],
    approval_decisions: tuple[ApprovalDecision, ...],
    task_lifecycle: TaskLifecycleRecord | None,
    watchdog_signals: tuple[TaskWatchdogSignal, ...],
    status: str,
    recovery_handoff: str,
) -> SubagentRuntimeSession:
    """Build the v52 runtime session from collaboration execution evidence.

    This function composes the collaboration plan, execution evidence, and
    communication trail into one session object. It is the best place to study
    how the project intends future asynchronous multi-agent runtime to look.
    """

    session_id = f"subagent-session-{len(plan.delegations):02d}"
    messages: list[SubagentMessageEnvelope] = []
    transitions: list[SubagentStateTransition] = []
    queue_items: list[SubagentQueueItem] = []
    inbox_entries: list[SubagentInboxEntry] = []
    outbox_entries: list[SubagentOutboxEntry] = []
    claim_records: list[SubagentClaimRecord] = []
    current_state = "created"
    message_order = 1
    transition_order = 1
    last_role = plan.assigned_roles[0].name if plan.assigned_roles else "parent_agent"
    current_delegation_id = plan.delegations[-1].delegation_id if plan.delegations else "none"

    transitions.append(
        build_state_transition(
            session_id=session_id,
            from_state=current_state,
            to_state="pending",
            actor="parent_agent",
            reason="Initialized the async delegation queue from the collaboration plan.",
            order=transition_order,
        )
    )
    current_state = "pending"
    transition_order += 1

    for delegation, execution, returned in zip(plan.delegations, executions, returns, strict=True):
        source_role = "parent_agent" if delegation.order == 1 else plan.delegations[delegation.order - 2].role.name
        final_queue_status = execution.status if execution.status in {"blocked", "failed"} else "completed"
        queue_item = build_queue_item(
            session_id=session_id,
            delegation=delegation,
            from_role=source_role,
            status=final_queue_status,
            order=delegation.order,
        )
        queue_items.append(queue_item)
        inbox_entries.append(
            build_inbox_entry(
                session_id=session_id,
                role_name=delegation.role.name,
                queue_item_id=queue_item.queue_item_id,
                delegation_id=delegation.delegation_id,
                status=final_queue_status,
                summary=delegation.child_task,
                order=delegation.order,
            )
        )
        claim_records.append(
            build_claim_record(
                session_id=session_id,
                queue_item_id=queue_item.queue_item_id,
                delegation_id=delegation.delegation_id,
                role_name=delegation.role.name,
                status="claimed" if execution.status == "completed" else execution.status,
                note=f"{delegation.role.name} claimed {queue_item.queue_item_id} for execution.",
                order=delegation.order,
            )
        )
        transitions.append(
            build_state_transition(
                session_id=session_id,
                from_state=current_state,
                to_state="running",
                actor=delegation.role.name,
                reason=f"Delegation {delegation.delegation_id} was claimed by {delegation.role.name}.",
                order=transition_order,
            )
        )
        current_state = "running"
        transition_order += 1
        last_role = delegation.role.name

        messages.append(
            build_message_envelope(
                session_id=session_id,
                from_role=source_role,
                to_role=delegation.role.name,
                message_type="delegation" if delegation.order == 1 else "handoff",
                summary=delegation.child_task,
                referenced_records=(delegation.delegation_id,),
                status="consumed" if execution.status != "blocked" else "blocked",
                order=message_order,
            )
        )
        message_order += 1

        if execution.status in {"failed", "blocked"}:
            terminal_state = "blocked" if execution.status == "blocked" else "failed"
            outbox_entries.append(
                build_outbox_entry(
                    session_id=session_id,
                    role_name=delegation.role.name,
                    delegation_id=delegation.delegation_id,
                    destination_role="parent_agent",
                    status=terminal_state,
                    summary=recovery_handoff,
                    order=delegation.order,
                )
            )
            messages.append(
                build_message_envelope(
                    session_id=session_id,
                    from_role=delegation.role.name,
                    to_role="parent_agent",
                    message_type="blocked" if execution.status == "blocked" else "recovery",
                    summary=recovery_handoff,
                    referenced_records=(delegation.delegation_id, returned.return_id),
                    status=terminal_state,
                    order=message_order,
                )
            )
            message_order += 1
            transitions.append(
                build_state_transition(
                    session_id=session_id,
                    from_state=current_state,
                    to_state=terminal_state,
                    actor=delegation.role.name,
                    reason=execution.verification_note,
                    order=transition_order,
                )
            )
            current_state = terminal_state
            break

        outbox_entries.append(
            build_outbox_entry(
                session_id=session_id,
                role_name=delegation.role.name,
                delegation_id=delegation.delegation_id,
                destination_role=returned.next_handoff,
                status="completed",
                summary=returned.summary,
                order=delegation.order,
            )
        )
        transitions.append(
            build_state_transition(
                session_id=session_id,
                from_state=current_state,
                to_state="completed",
                actor=delegation.role.name,
                reason=returned.summary,
                order=transition_order,
            )
        )
        current_state = "completed"
        transition_order += 1

        messages.append(
            build_message_envelope(
                session_id=session_id,
                from_role=delegation.role.name,
                to_role=returned.next_handoff,
                message_type="return",
                summary=returned.summary,
                referenced_records=(returned.return_id,),
                status="emitted",
                order=message_order,
            )
        )
        message_order += 1

    if status == "completed":
        transitions.append(
            build_state_transition(
                session_id=session_id,
                from_state=current_state,
                to_state="completed",
                actor="parent_agent",
                reason="All delegated roles returned bounded outputs to the parent flow.",
                order=transition_order,
            )
        )
        current_state = "completed"

    context_source = plan.contracts[-1] if plan.contracts else None
    active_role = last_role if status == "failed" else "parent_agent"
    if status == "blocked":
        active_role = last_role
    if context_source is None:
        context_boundary = build_context_boundary(
            session_id=session_id,
            parent_role="parent_agent",
            active_role=active_role,
            objective=plan.objective,
            required_inputs=(),
            expected_outputs=(),
        )
    else:
        context_boundary = build_context_boundary(
            session_id=session_id,
            parent_role="parent_agent",
            active_role=active_role,
            objective=context_source.objective,
            required_inputs=context_source.required_inputs,
            expected_outputs=context_source.expected_outputs,
        )

    return SubagentRuntimeSession(
        session_id=session_id,
        objective=plan.objective,
        parent_role="parent_agent",
        child_roles=tuple(role.name for role in plan.assigned_roles),
        active_role=active_role,
        current_delegation_id=current_delegation_id,
        execution_mode="deterministic-async-delegation",
        status=status,
        terminal_reason="All delegated tasks completed." if status == "completed" else recovery_handoff,
        context_boundary=context_boundary,
        messages=tuple(messages),
        transitions=tuple(transitions),
        queue_items=tuple(queue_items),
        inbox_entries=tuple(inbox_entries),
        outbox_entries=tuple(outbox_entries),
        claim_records=tuple(claim_records),
        guarded_handoffs=guarded_handoffs,
        approval_requests=approval_requests,
        approval_decisions=approval_decisions,
        task_lifecycle=task_lifecycle,
        watchdog_signals=watchdog_signals,
    )


def describe_subagents() -> str:
    """Render available subagents as a readable text block.

    Returns:
        A short, human-friendly summary of the built-in roles and their
        handoff rules.
    """

    lines = ["Available subagents:"]
    for role in get_default_subagents():
        lines.append(f"- {role.name}: {role.responsibility}")
        lines.append(f"  Handoff: {role.handoff_rule}")
        lines.append(f"  Input boundary: {role.input_boundary}")
        lines.append(f"  Output boundary: {role.output_boundary}")
    return "\n".join(lines)


def build_collaboration_plan(user_input: str) -> CollaborationPlan:
    """Build a simple collaboration plan for a user request.

    The planner is intentionally deterministic. It uses the user request text
    to choose between:

    - a teaching-only plan for explanation-oriented tasks
    - a teacher-plus-coding plan for implementation-oriented tasks

    Example:
        >>> plan = build_collaboration_plan("Explain the agent runtime")
        >>> plan.assigned_roles[0].name
        'teacher_agent'
    """

    roles = get_default_subagents()
    lowered = user_input.lower()
    code_task = any(
        keyword in lowered
        for keyword in (
            "implement",
            "fix",
            "test",
            "code",
            "bug",
            "review",
            "delete",
            "remove",
            "overwrite",
            "write",
            "publish",
            "commit",
        )
    )

    if code_task:
        selected_roles = roles
        steps = (
            "Teacher Agent defines the objective, input boundary, and safe handoff rules.",
            "Coding Agent implements the smallest safe change and returns verification evidence.",
            "Teacher Agent reviews the result and records the learning checkpoint.",
        )
    else:
        selected_roles = (roles[0],)
        steps = (
            "Teacher Agent explains the concept and records the input/output boundary.",
            "Teacher Agent identifies the learning checkpoint and whether a coding handoff is needed.",
        )

    contracts = tuple(build_subagent_task_contract(role, user_input) for role in selected_roles)
    delegations = tuple(
        build_delegation_record(user_input, role, contract, order=index)
        for index, (role, contract) in enumerate(zip(selected_roles, contracts, strict=True), start=1)
    )
    return CollaborationPlan(
        objective=user_input,
        assigned_roles=selected_roles,
        contracts=contracts,
        delegations=delegations,
        steps=steps,
    )


def execute_collaboration_plan(user_input: str, approval_override: str | None = None) -> CollaborationPlan:
    """Execute the deterministic collaboration plan and return structured evidence.

    The execution is still simulated, but the evidence objects are real. That
    makes the module useful for learning the shape of a future runtime without
    requiring a live multi-agent backend yet.
    """

    plan = build_collaboration_plan(user_input)
    handoffs: list[SubagentHandoffRecord] = []
    guarded_handoffs: list[GuardedHandoffRecord] = []
    returns: list[SubagentReturnRecord] = []
    executions: list[SubagentExecutionRecord] = []
    milestones: list[TaskMilestoneRecord] = []
    watchdog_signals: list[TaskWatchdogSignal] = []
    lowered = user_input.lower()
    failed = "ambiguous" in lowered or "unclear" in lowered or "underspecified" in lowered
    blocked = "blocked" in lowered or "offline" in lowered or "unavailable" in lowered
    lifecycle_requested = any(
        keyword in lowered
        for keyword in ("pause", "resume", "expire", "expired", "abandon", "abandoned", "watchdog", "stalled", "timeout")
    )
    code_task = len(plan.assigned_roles) > 1
    risk = build_risk_classification(user_input)
    target_role = plan.delegations[-1].role.name if plan.delegations else "teacher_agent"
    approval_request = build_approval_request(
        session_id=f"subagent-session-{len(plan.delegations):02d}",
        requester_role="parent_agent",
        target_role=target_role,
        requested_action=f"Allow guarded handoff to {target_role}",
        objective=plan.objective,
        risk=risk,
    )
    if approval_override in {"approved", "rejected", "revise_required"}:
        approval_decision_name = approval_override
    elif risk.requires_approval:
        approval_decision_name = "revise_required"
    else:
        approval_decision_name = "approved"
    approval_rationale = (
        "The objective is safe to proceed after review."
        if approval_decision_name == "approved"
        else "The objective is high risk and must be revised before the guarded handoff can continue."
    )
    approval_decision = build_approval_decision(
        request=approval_request,
        decision=approval_decision_name,
        rationale=approval_rationale,
        next_action=(
            "Continue the guarded handoff."
            if approval_decision_name == "approved"
            else "Revise the objective and resubmit for approval."
        ),
    )
    approved = approval_decision.decision == "approved"
    if plan.delegations and len(plan.delegations) > 1:
        guarded_handoffs.append(
            build_guarded_handoff_record(
                from_role=plan.delegations[0].role.name,
                to_role=plan.delegations[1].role.name,
                approval_status=approval_decision.decision,
                risk_level=risk.risk_level,
                reason="Guarded handoff from review role to implementation role.",
                payload_summary=plan.delegations[1].child_task,
                fallback_action=approval_decision.next_action,
                order=1,
            )
        )

    for index, delegation in enumerate(plan.delegations, start=1):
        next_role = plan.delegations[index].role.name if index < len(plan.delegations) else "parent_agent"
        if delegation.role.name == "teacher_agent":
            outputs = ("objective clarification", "safe handoff rule", "learning checkpoint")
            verification = "Clarified the task boundary and prepared the next handoff."
            recovery = delegation.contract.recovery_handoff
            status = "completed"
        elif not approved:
            outputs = ("approval gate blocked",)
            verification = approval_decision.rationale
            recovery = approval_decision.next_action
            status = "blocked"
        elif blocked:
            outputs = ("queued implementation note", "blocked dependency note")
            verification = "Execution was claimed but is currently blocked in the agent inbox awaiting a safe resume."
            recovery = "Retry the blocked task from the coding_agent inbox after unblocking the dependency, or hand it back to teacher_agent for replanning."
            status = "blocked"
        elif failed:
            outputs = ("blocked implementation note",)
            verification = "Implementation was blocked because the request was underspecified."
            recovery = delegation.contract.recovery_handoff
            status = "failed"
        else:
            outputs = ("code patch", "test updates", "verification evidence")
            verification = "Implemented the bounded change and prepared verification evidence."
            recovery = delegation.contract.recovery_handoff
            status = "completed"

        milestones.append(
            build_task_milestone_record(
                session_id=approval_request.session_id,
                title=f"{delegation.role.name} milestone {index:02d}",
                status="reached" if status == "completed" else status,
                evidence_summary=verification,
                order=index,
            )
        )

        executions.append(
            build_execution_record(
                delegation,
                status=status,
                produced_outputs=outputs,
                verification_note=verification,
                recovery_action=recovery,
            )
        )
        returns.append(
            build_return_record(
                delegation.role.name,
                status,
                outputs,
                verification,
                next_role,
                index,
            )
        )
        if index < len(plan.delegations):
            handoffs.append(
                build_handoff_record(
                    delegation.role.name,
                    next_role,
                    reason=(
                        f"{delegation.role.name} completed its bounded responsibility."
                        if approved or delegation.role.name == "teacher_agent"
                        else "The guarded handoff was paused by approval control."
                    ),
                    payload_summary=verification,
                order=index,
            )
        )
        if status == "failed":
            watchdog_signals.append(
                build_task_watchdog_signal(
                    session_id=approval_request.session_id,
                    signal_type="failed",
                    severity="high",
                    summary="Task execution failed before the long-horizon workflow could complete.",
                    recommended_action=recovery,
                    order=len(watchdog_signals) + 1,
                )
            )
            runtime_session = build_runtime_session(
                plan=plan,
                handoffs=tuple(handoffs),
                guarded_handoffs=tuple(guarded_handoffs),
                returns=tuple(returns),
                executions=tuple(executions),
                approval_requests=(approval_request,),
                approval_decisions=(approval_decision,),
                task_lifecycle=build_task_lifecycle_record(
                    session_id=approval_request.session_id,
                    objective=plan.objective,
                    state="failed",
                    health="failed",
                    progress_stage="execution",
                    current_milestone=milestones[-1].title,
                    paused_reason="",
                    resume_hint="Resume from the latest checkpoint after clarifying the request.",
                    terminal_reason=recovery,
                    next_safe_action=recovery,
                    milestones=tuple(milestones),
                ),
                watchdog_signals=tuple(watchdog_signals),
                status="failed",
                recovery_handoff=recovery,
            )
            return CollaborationPlan(
                objective=plan.objective,
                assigned_roles=plan.assigned_roles,
                contracts=plan.contracts,
                delegations=plan.delegations,
                steps=plan.steps,
                handoffs=tuple(handoffs),
                guarded_handoffs=tuple(guarded_handoffs),
                returns=tuple(returns),
                executions=tuple(executions),
                risk=risk,
                approval_request=approval_request,
                approval_decision=approval_decision,
                task_lifecycle=build_task_lifecycle_record(
                    session_id=approval_request.session_id,
                    objective=plan.objective,
                    state="failed",
                    health="failed",
                    progress_stage="execution",
                    current_milestone=milestones[-1].title,
                    paused_reason="",
                    resume_hint="Resume from the latest checkpoint after clarifying the request.",
                    terminal_reason=recovery,
                    next_safe_action=recovery,
                    milestones=tuple(milestones),
                ),
                watchdog_signals=tuple(watchdog_signals),
                status="failed",
                recovery_handoff=recovery,
                runtime_session=runtime_session,
            )
        if status == "blocked":
            watchdog_signals.append(
                build_task_watchdog_signal(
                    session_id=approval_request.session_id,
                    signal_type="stalled",
                    severity="medium",
                    summary="The long-horizon task is blocked inside the inbox and needs a safe resume path.",
                    recommended_action=recovery,
                    order=len(watchdog_signals) + 1,
                )
            )
            runtime_session = build_runtime_session(
                plan=plan,
                handoffs=tuple(handoffs),
                guarded_handoffs=tuple(guarded_handoffs),
                returns=tuple(returns),
                executions=tuple(executions),
                approval_requests=(approval_request,),
                approval_decisions=(approval_decision,),
                task_lifecycle=build_task_lifecycle_record(
                    session_id=approval_request.session_id,
                    objective=plan.objective,
                    state="blocked",
                    health="stalled",
                    progress_stage="execution",
                    current_milestone=milestones[-1].title,
                    paused_reason="The task is blocked in the agent inbox.",
                    resume_hint="Unblock the dependency, then resume from the last checkpoint.",
                    terminal_reason=recovery,
                    next_safe_action=recovery,
                    milestones=tuple(milestones),
                ),
                watchdog_signals=tuple(watchdog_signals),
                status="blocked",
                recovery_handoff=recovery,
            )
            return CollaborationPlan(
                objective=plan.objective,
                assigned_roles=plan.assigned_roles,
                contracts=plan.contracts,
                delegations=plan.delegations,
                steps=plan.steps,
                handoffs=tuple(handoffs),
                guarded_handoffs=tuple(guarded_handoffs),
                returns=tuple(returns),
                executions=tuple(executions),
                risk=risk,
                approval_request=approval_request,
                approval_decision=approval_decision,
                task_lifecycle=build_task_lifecycle_record(
                    session_id=approval_request.session_id,
                    objective=plan.objective,
                    state="blocked",
                    health="stalled",
                    progress_stage="execution",
                    current_milestone=milestones[-1].title,
                    paused_reason="The task is blocked in the agent inbox.",
                    resume_hint="Unblock the dependency, then resume from the last checkpoint.",
                    terminal_reason=recovery,
                    next_safe_action=recovery,
                    milestones=tuple(milestones),
                ),
                watchdog_signals=tuple(watchdog_signals),
                status="blocked",
                recovery_handoff=recovery,
                runtime_session=runtime_session,
            )

    lifecycle_state = "completed"
    lifecycle_health = "healthy"
    lifecycle_stage = "delivery"
    paused_reason = ""
    resume_hint = "Use the latest milestone and continue the next pending task."
    terminal_reason = "All delegated tasks completed."
    next_safe_action = "Persist the checkpoint and start the next bounded task."
    if lifecycle_requested and "pause" in lowered:
        lifecycle_state = "paused"
        lifecycle_health = "paused"
        lifecycle_stage = "pause"
        paused_reason = "The task was deliberately paused for a later resume."
        resume_hint = "Resume from the latest milestone after confirming the remaining scope."
        terminal_reason = "The task was paused by request."
        next_safe_action = "Resume the task from the latest checkpoint."
        watchdog_signals.append(
            build_task_watchdog_signal(
                session_id=approval_request.session_id,
                signal_type="paused",
                severity="low",
                summary="The task is intentionally paused and waiting for a later resume.",
                recommended_action=resume_hint,
                order=len(watchdog_signals) + 1,
            )
        )
    elif lifecycle_requested and any(keyword in lowered for keyword in ("resume",)):
        lifecycle_state = "resumed"
        lifecycle_health = "healthy"
        lifecycle_stage = "resume"
        terminal_reason = "The task was resumed from a paused state."
        next_safe_action = "Continue the next pending milestone."
        watchdog_signals.append(
            build_task_watchdog_signal(
                session_id=approval_request.session_id,
                signal_type="healthy",
                severity="low",
                summary="The task has resumed and the runtime can continue safely.",
                recommended_action=next_safe_action,
                order=len(watchdog_signals) + 1,
            )
        )
    elif lifecycle_requested and any(keyword in lowered for keyword in ("expire", "expired")):
        lifecycle_state = "expired"
        lifecycle_health = "expired"
        lifecycle_stage = "expired"
        paused_reason = "The task expired before it could reach completion."
        resume_hint = "Create a fresh task or restart from a narrower scope."
        terminal_reason = "The task expired while waiting for further progress."
        next_safe_action = "Abandon the expired task and open a new run if needed."
        watchdog_signals.append(
            build_task_watchdog_signal(
                session_id=approval_request.session_id,
                signal_type="expired",
                severity="high",
                summary="The task expired and should not be resumed without re-planning.",
                recommended_action=next_safe_action,
                order=len(watchdog_signals) + 1,
            )
        )
    elif lifecycle_requested and any(keyword in lowered for keyword in ("abandon", "abandoned")):
        lifecycle_state = "abandoned"
        lifecycle_health = "abandoned"
        lifecycle_stage = "abandon"
        paused_reason = "The task was intentionally abandoned."
        resume_hint = "Start a new task with a narrower scope."
        terminal_reason = "The task was abandoned by request."
        next_safe_action = "Create a new bounded collaboration plan."
        watchdog_signals.append(
            build_task_watchdog_signal(
                session_id=approval_request.session_id,
                signal_type="abandoned",
                severity="medium",
                summary="The task was intentionally abandoned and should not be resumed as-is.",
                recommended_action=next_safe_action,
                order=len(watchdog_signals) + 1,
            )
        )
    elif lifecycle_requested and any(keyword in lowered for keyword in ("watchdog", "stalled", "timeout")):
        lifecycle_state = "paused"
        lifecycle_health = "stalled"
        lifecycle_stage = "watchdog"
        paused_reason = "A watchdog signal detected stalled long-horizon progress."
        resume_hint = "Inspect the blocked dependency, then resume from the latest checkpoint."
        terminal_reason = "The watchdog paused the task to preserve safe recovery."
        next_safe_action = "Inspect the stall cause before resuming."
        watchdog_signals.append(
            build_task_watchdog_signal(
                session_id=approval_request.session_id,
                signal_type="stalled",
                severity="high",
                summary="A watchdog-style stall was detected in the long-horizon task.",
                recommended_action=next_safe_action,
                order=len(watchdog_signals) + 1,
            )
        )

    task_lifecycle = build_task_lifecycle_record(
        session_id=approval_request.session_id,
        objective=plan.objective,
        state=lifecycle_state,
        health=lifecycle_health,
        progress_stage=lifecycle_stage,
        current_milestone=milestones[-1].title if milestones else "none",
        paused_reason=paused_reason,
        resume_hint=resume_hint,
        terminal_reason=terminal_reason,
        next_safe_action=next_safe_action,
        milestones=tuple(milestones),
    )
    final_status = lifecycle_state if lifecycle_state in {"paused", "expired", "abandoned"} else "completed"

    runtime_session = build_runtime_session(
        plan=plan,
        handoffs=tuple(handoffs),
        guarded_handoffs=tuple(guarded_handoffs),
        returns=tuple(returns),
        executions=tuple(executions),
        approval_requests=(approval_request,),
        approval_decisions=(approval_decision,),
        task_lifecycle=task_lifecycle,
        watchdog_signals=tuple(watchdog_signals),
        status=final_status,
        recovery_handoff=next_safe_action if final_status != "completed" else "none",
    )
    return CollaborationPlan(
        objective=plan.objective,
        assigned_roles=plan.assigned_roles,
        contracts=plan.contracts,
        delegations=plan.delegations,
        steps=plan.steps,
        handoffs=tuple(handoffs),
        guarded_handoffs=tuple(guarded_handoffs),
        returns=tuple(returns),
        executions=tuple(executions),
        risk=risk,
        approval_request=approval_request,
        approval_decision=approval_decision,
        task_lifecycle=task_lifecycle,
        watchdog_signals=tuple(watchdog_signals),
        status=final_status,
        recovery_handoff=next_safe_action if final_status != "completed" else "none",
        runtime_session=runtime_session,
    )
