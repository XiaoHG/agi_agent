"""Project-level assistant that combines the learned agent capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from evals.runner import build_eval_report, load_eval_cases, run_eval_cases

from .core import AgentRun, WorkspaceAgent


@dataclass(frozen=True)
class ProjectLearningReport:
    """Structured result for the comprehensive project demo."""

    objective: str  # 本次综合项目演示的任务目标
    readme_summary: str  # README 读取结果摘要
    docs_context: str  # 本地 RAG 检索结果摘要
    mcp_summary: str  # MCP workspace summary 结果摘要
    skill_plan: str  # Skill 选择与执行步骤摘要
    collaboration_plan: str  # Subagent 协作计划摘要
    regression_report: dict[str, Any]  # 回归评估报告

    def to_text(self) -> str:
        """Render the report as a deterministic user-facing summary."""

        return (
            f"Objective: {self.objective}\n\n"
            "Capability chain:\n"
            "1. File reading: completed\n"
            "2. Local RAG: completed\n"
            "3. MCP tool: completed\n"
            "4. Skill selection: completed\n"
            "5. Subagent planning: completed\n"
            "6. Regression eval: completed\n\n"
            f"README summary:\n{self.readme_summary}\n\n"
            f"Docs context:\n{self.docs_context}\n\n"
            f"MCP summary:\n{self.mcp_summary}\n\n"
            f"Skill plan:\n{self.skill_plan}\n\n"
            f"Collaboration plan:\n{self.collaboration_plan}\n\n"
            "Regression eval:\n"
            f"- Total: {self.regression_report['total']}\n"
            f"- Passed: {self.regression_report['passed']}\n"
            f"- Failed: {self.regression_report['failed']}"
        )


class ProjectLearningAssistant:
    """Small product prototype that coordinates existing project capabilities."""

    def __init__(self, workspace_root: Path | str = ".") -> None:
        self.workspace_root = Path(workspace_root).resolve()  # 统一使用绝对路径，避免 CLI 和测试路径不一致
        self.agent = WorkspaceAgent(self.workspace_root)  # 复用已有 Agent 主循环，不重复实现路由和工具调用

    def run(self, objective: str = "Build a project learning assistant report.") -> ProjectLearningReport:
        """Run the comprehensive learning-assistant workflow."""

        # 1. 文件读取：确认项目目标和学习路线
        readme_run = self.agent.run("Read README.md and summarize the project learning goals.")

        # 2. 本地 RAG：从项目文档中检索综合项目所需上下文
        docs_run = self.agent.run("Search docs for workflow RAG MCP skills subagent eval.")

        # 3. MCP：通过本地协议工具获取工作区摘要
        mcp_run = self.agent.run("Use MCP workspace summary.")

        # 4. Skill：为代码评审类任务选择可复用技能
        skill_run = self.agent.run("Select a skill for code review.")

        # 5. Subagent：规划 Teacher Agent 和 Coding Agent 的协作方式
        collaboration_run = self.agent.run("Plan subagent collaboration for a code review.")

        # 6. Eval：复用现有回归用例验证主 Agent 没有被综合项目破坏
        regression_report = self._run_regression_eval()

        return ProjectLearningReport(
            objective=objective,
            readme_summary=self._preview_run(readme_run),
            docs_context=self._preview_run(docs_run),
            mcp_summary=self._preview_run(mcp_run),
            skill_plan=self._preview_run(skill_run),
            collaboration_plan=self._preview_run(collaboration_run),
            regression_report=regression_report,
        )

    def _run_regression_eval(self) -> dict[str, Any]:
        """Run the deterministic regression suite for this project demo."""

        cases_path = self.workspace_root / "evals" / "regression_cases.json"
        cases = load_eval_cases(cases_path)
        results = run_eval_cases(self.agent, cases)
        return build_eval_report(results)

    def _preview_run(self, run: AgentRun, limit: int = 360) -> str:
        """Convert an AgentRun answer into a compact single-line preview."""

        normalized = " ".join(run.answer.split())
        if len(normalized) <= limit:
            return normalized
        return normalized[: limit - 15] + "... (truncated)"
