"""Deterministic subagent planning for learning multi-agent boundaries."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class SubagentSpec:
    """Role definition for one project subagent."""

    name: str               # 子 Agent 的角色名
    responsibility: str     # 该角色负责的核心职责
    handoff_rule: str       # 什么时候切换给它
    input_boundary: str     # 它允许接收的输入边界
    output_boundary: str    # 它必须产出的输出边界

    def to_dict(self) -> dict[str, Any]:
        """Render the role definition as JSON-ready data."""

        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "handoff_rule": self.handoff_rule,
            "input_boundary": self.input_boundary,
            "output_boundary": self.output_boundary,
        }


@dataclass(frozen=True)
class SubagentTaskContract:
    """Input/output contract for a delegated subtask."""

    role_name: str                      # 该子任务分配给哪个角色
    objective: str                      # 该子任务的明确目标
    input_boundary: str                 # 该子任务可消费的信息边界
    required_inputs: tuple[str, ...]    # 完成子任务所需的最小输入
    output_boundary: str                # 该子任务输出的责任边界
    expected_outputs: tuple[str, ...]   # 该子任务预期交付物
    recovery_handoff: str               # 失败或不明确时如何交接恢复

    def to_dict(self) -> dict[str, Any]:
        """Render the contract as JSON-ready data."""

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
        """Render the contract as a compact readable block."""

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
    """Structured record for one delegated child task."""

    delegation_id: str              # 本次委派记录的唯一标识
    parent_objective: str           # 上层主任务目标
    role: SubagentSpec              # 被委派的子 Agent 角色
    contract: SubagentTaskContract  # 这次委派绑定的任务契约
    status: str                     # 当前委派状态，例如 planned / completed / failed
    child_task: str                 # 实际下发给子 Agent 的任务描述
    order: int                      # 该委派在协作流程中的顺序
    notes: str                      # 额外说明，通常记录恢复或交接提示

    def to_dict(self) -> dict[str, Any]:
        """Render the delegation record as JSON-ready data."""

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
        """Render the delegation record as a compact readable block."""

        return (
            f"- Delegation {self.delegation_id} [{self.status}] -> {self.role.name}\n"
            f"  Child task: {self.child_task}\n"
            f"  Notes: {self.notes}"
        )


@dataclass(frozen=True)
class SubagentHandoffRecord:
    """Structured handoff from one role to another."""

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
    """Structured return from one subagent back to the parent flow."""

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
    """Execution evidence for one delegated subtask."""

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
class CollaborationPlan:
    """A small ordered plan that assigns work to subagents."""

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
        }

    def to_text(self) -> str:
        """Render the collaboration plan."""

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
        lines.append("Workflow:")
        for index, step in enumerate(self.steps, start=1):
            lines.append(f"{index}. {step}")
        lines.append(f"Plan status: {self.status}")
        if self.recovery_handoff:
            lines.append(f"Recovery handoff: {self.recovery_handoff}")
        return "\n".join(lines)


def get_default_subagents() -> tuple[SubagentSpec, ...]:
    """Return the default project subagents."""

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
    """Build a deterministic contract for one subagent role."""

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
    """Build a deterministic delegation record for a child task."""

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
    """Build a deterministic handoff record between two roles."""

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
    """Build a deterministic return record for one role."""

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
    """Build a deterministic child-task execution record."""

    return SubagentExecutionRecord(
        delegation_id=delegation.delegation_id,
        role_name=delegation.role.name,
        status=status,
        child_task=delegation.child_task,
        produced_outputs=produced_outputs,
        verification_note=verification_note,
        recovery_action=recovery_action,
    )


def describe_subagents() -> str:
    """Render available subagents."""

    lines = ["Available subagents:"]
    for role in get_default_subagents():
        lines.append(f"- {role.name}: {role.responsibility}")
        lines.append(f"  Handoff: {role.handoff_rule}")
        lines.append(f"  Input boundary: {role.input_boundary}")
        lines.append(f"  Output boundary: {role.output_boundary}")
    return "\n".join(lines)


def build_collaboration_plan(user_input: str) -> CollaborationPlan:
    """Build a simple collaboration plan for a user request."""

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
    """Execute the deterministic collaboration plan and return structured evidence."""

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
    )
