from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .models import Badcase, OptimizationAction
from .optimizer import ThreeStageOptimizer


@dataclass(frozen=True)
class AgentStep:
    name: str
    status: str
    detail: str


@dataclass
class AgentRun:
    steps: list[AgentStep] = field(default_factory=list)
    actions: list[OptimizationAction] = field(default_factory=list)
    pending_review: list[OptimizationAction] = field(default_factory=list)
    reflection: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "steps": [step.__dict__ for step in self.steps],
            "actions": [action.__dict__ for action in self.actions],
            "pending_review": [action.__dict__ for action in self.pending_review],
            "reflection": self.reflection,
        }


class KnowledgeOperationsAgent:
    """Auditable Plan-Execute-Reflection wrapper around the three stages."""

    def __init__(self, optimizer: ThreeStageOptimizer) -> None:
        self.optimizer = optimizer

    def run(self, badcases: list[Badcase] | None = None) -> AgentRun:
        result = AgentRun()
        result.steps.append(AgentStep("plan", "completed", "规划知识体检、Badcase 策略和问法补全三阶段"))
        report = self.optimizer.run(badcases)
        candidates = report.badcase_actions + report.expansion_actions
        result.steps.append(AgentStep("execute", "completed", f"生成 {len(candidates)} 个候选动作"))
        result.actions = [item for item in candidates if not item.requires_review and item.risk == "low"]
        result.pending_review = [item for item in candidates if item not in result.actions]
        result.reflection = {
            "health_finding_count": len(report.health_findings),
            "auto_executable_count": len(result.actions),
            "review_required_count": len(result.pending_review),
            "guardrail": "candidate actions require evaluation before publishing",
        }
        result.steps.append(AgentStep("reflection", "completed", "复核动作风险并分流人工审核"))
        return result
