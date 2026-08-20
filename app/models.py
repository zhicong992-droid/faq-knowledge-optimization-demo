from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


ActionKind = Literal[
    "add_similar_question",
    "rewrite_question",
    "delete_question",
    "create_category",
    "move_faq",
]


@dataclass(frozen=True)
class FAQ:
    faq_id: str
    category: str
    question: str
    answer: str
    similar_questions: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class Badcase:
    query: str
    expected_faq_id: str | None = None
    reason: str = "低置信度"


@dataclass(frozen=True)
class RetrievalHit:
    faq_id: str
    question: str
    category: str
    score: float
    channels: tuple[str, ...] = ()


@dataclass(frozen=True)
class HealthFinding:
    finding_type: str
    severity: Literal["low", "medium", "high"]
    faq_ids: tuple[str, ...]
    detail: str


@dataclass(frozen=True)
class OptimizationAction:
    kind: ActionKind
    faq_id: str
    payload: dict[str, Any]
    risk: Literal["low", "medium", "high"] = "low"
    requires_review: bool = False


@dataclass
class OptimizationReport:
    health_findings: list[HealthFinding] = field(default_factory=list)
    badcase_actions: list[OptimizationAction] = field(default_factory=list)
    expansion_actions: list[OptimizationAction] = field(default_factory=list)
    metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "health_findings": [asdict(item) for item in self.health_findings],
            "badcase_actions": [asdict(item) for item in self.badcase_actions],
            "expansion_actions": [asdict(item) for item in self.expansion_actions],
            "metrics": self.metrics,
        }
