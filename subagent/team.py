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
    CollaborationPlan
      assigned_roles
      contracts
      delegations
      handoffs
      returns
      executions
      runtime_session
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
    returns: tuple[SubagentReturnRecord, ...] = ()          # 子任务回传记录
    executions: tuple[SubagentExecutionRecord, ...] = ()    # 子任务执行轨迹
    status: str = "planned"                                 # planned / completed / failed
    recovery_handoff: str = ""                              # 整体失败时的恢复动作
    runtime_session: SubagentRuntimeSession | None = None   # v51 多 Agent runtime session

    def to_dict(self) -> dict[str, Any]:
        """Render the collaboration plan as JSON-ready data."""

        return {
            "objective": self.objective,
            "assigned_roles": [role.to_dict() for role in self.assigned_roles],
            "contracts": [contract.to_dict() for contract in self.contracts],
            "delegations": [delegation.to_dict() for delegation in self.delegations],
            "steps": list(self.steps),
            "handoffs": [handoff.to_dict() for handoff in self.handoffs],
            "returns": [item.to_dict() for item in self.returns],
            "executions": [execution.to_dict() for execution in self.executions],
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
        if self.executions:
            lines.append("Executions:")
            for execution in self.executions:
                lines.append(
                    f"- {execution.delegation_id} [{execution.status}] {execution.role_name}: {execution.verification_note}"
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


def build_runtime_session(
    *,
    plan: CollaborationPlan,
    handoffs: tuple[SubagentHandoffRecord, ...],
    returns: tuple[SubagentReturnRecord, ...],
    executions: tuple[SubagentExecutionRecord, ...],
    status: str,
    recovery_handoff: str,
) -> SubagentRuntimeSession:
    """Build the v51 runtime session from collaboration execution evidence.

    This function composes the collaboration plan, execution evidence, and
    communication trail into one session object. It is the best place to study
    how the project intends future asynchronous multi-agent runtime to look.
    """

    session_id = f"subagent-session-{len(plan.delegations):02d}"
    messages: list[SubagentMessageEnvelope] = []
    transitions: list[SubagentStateTransition] = []
    current_state = "created"
    message_order = 1
    transition_order = 1
    last_role = plan.assigned_roles[0].name if plan.assigned_roles else "parent_agent"
    current_delegation_id = plan.delegations[-1].delegation_id if plan.delegations else "none"

    transitions.append(
        build_state_transition(
            session_id=session_id,
            from_state=current_state,
            to_state="planned",
            actor="parent_agent",
            reason="Initialized the runtime session from the collaboration plan.",
            order=transition_order,
        )
    )
    current_state = "planned"
    transition_order += 1

    for delegation, execution, returned in zip(plan.delegations, executions, returns, strict=True):
        transitions.append(
            build_state_transition(
                session_id=session_id,
                from_state=current_state,
                to_state=f"running_{delegation.role.name}",
                actor=delegation.role.name,
                reason=f"Delegation {delegation.delegation_id} entered execution.",
                order=transition_order,
            )
        )
        current_state = f"running_{delegation.role.name}"
        transition_order += 1
        last_role = delegation.role.name

        messages.append(
            build_message_envelope(
                session_id=session_id,
                from_role="parent_agent" if delegation.order == 1 else plan.delegations[delegation.order - 2].role.name,
                to_role=delegation.role.name,
                message_type="delegation" if delegation.order == 1 else "handoff",
                summary=delegation.child_task,
                referenced_records=(delegation.delegation_id,),
                status="consumed",
                order=message_order,
            )
        )
        message_order += 1

        if execution.status == "failed":
            messages.append(
                build_message_envelope(
                    session_id=session_id,
                    from_role=delegation.role.name,
                    to_role="parent_agent",
                    message_type="recovery",
                    summary=recovery_handoff,
                    referenced_records=(delegation.delegation_id, returned.return_id),
                    status="emitted",
                    order=message_order,
                )
            )
            message_order += 1
            transitions.append(
                build_state_transition(
                    session_id=session_id,
                    from_state=current_state,
                    to_state="failed",
                    actor=delegation.role.name,
                    reason=execution.verification_note,
                    order=transition_order,
                )
            )
            current_state = "failed"
            break

        transitions.append(
            build_state_transition(
                session_id=session_id,
                from_state=current_state,
                to_state=f"returned_{delegation.role.name}",
                actor=delegation.role.name,
                reason=returned.summary,
                order=transition_order,
            )
        )
        current_state = f"returned_{delegation.role.name}"
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

    context_source = plan.contracts[-1] if status == "failed" and plan.contracts else (plan.contracts[-1] if plan.contracts else None)
    if status == "completed" and plan.contracts:
        context_source = plan.contracts[-1]
    active_role = last_role if status == "failed" else "parent_agent"
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
        execution_mode="deterministic-runtime-foundation",
        status=status,
        terminal_reason="All delegated tasks completed." if status == "completed" else recovery_handoff,
        context_boundary=context_boundary,
        messages=tuple(messages),
        transitions=tuple(transitions),
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
    code_task = any(keyword in lowered for keyword in ("implement", "fix", "test", "code", "bug", "review"))

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


def execute_collaboration_plan(user_input: str) -> CollaborationPlan:
    """Execute the deterministic collaboration plan and return structured evidence.

    The execution is still simulated, but the evidence objects are real. That
    makes the module useful for learning the shape of a future runtime without
    requiring a live multi-agent backend yet.
    """

    plan = build_collaboration_plan(user_input)
    handoffs: list[SubagentHandoffRecord] = []
    returns: list[SubagentReturnRecord] = []
    executions: list[SubagentExecutionRecord] = []
    lowered = user_input.lower()
    failed = "ambiguous" in lowered or "unclear" in lowered or "underspecified" in lowered

    for index, delegation in enumerate(plan.delegations, start=1):
        next_role = plan.delegations[index].role.name if index < len(plan.delegations) else "parent_agent"
        if delegation.role.name == "teacher_agent":
            outputs = ("objective clarification", "safe handoff rule", "learning checkpoint")
            verification = "Clarified the task boundary and prepared the next handoff."
            recovery = delegation.contract.recovery_handoff
            status = "completed"
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
                    reason=f"{delegation.role.name} completed its bounded responsibility.",
                    payload_summary=verification,
                    order=index,
                )
            )
        if status == "failed":
            runtime_session = build_runtime_session(
                plan=plan,
                handoffs=tuple(handoffs),
                returns=tuple(returns),
                executions=tuple(executions),
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
                returns=tuple(returns),
                executions=tuple(executions),
                status="failed",
                recovery_handoff=recovery,
                runtime_session=runtime_session,
            )

    runtime_session = build_runtime_session(
        plan=plan,
        handoffs=tuple(handoffs),
        returns=tuple(returns),
        executions=tuple(executions),
        status="completed",
        recovery_handoff="none",
    )
    return CollaborationPlan(
        objective=plan.objective,
        assigned_roles=plan.assigned_roles,
        contracts=plan.contracts,
        delegations=plan.delegations,
        steps=plan.steps,
        handoffs=tuple(handoffs),
        returns=tuple(returns),
        executions=tuple(executions),
        status="completed",
        recovery_handoff="none",
        runtime_session=runtime_session,
    )
