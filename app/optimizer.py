from __future__ import annotations

from collections import Counter, defaultdict
from dataclasses import dataclass
from typing import Protocol

from .models import Badcase, FAQ, HealthFinding, OptimizationAction, OptimizationReport
from .retrieval import HybridRetriever, tokenize


class QuestionGenerator(Protocol):
    def generate(self, faq: FAQ) -> list[str]: ...


class RuleQuestionGenerator:
    def generate(self, faq: FAQ) -> list[str]:
        return [
            f"请问如何办理{faq.question.lstrip('如何')}？",
            f"我想了解{faq.question.rstrip('？')}的具体步骤",
            f"如果线上操作失败，{faq.question.rstrip('？')}还有什么办法？",
        ]


@dataclass
class ThreeStageOptimizer:
    faqs: list[FAQ]
    generator: QuestionGenerator | None = None

    def __post_init__(self) -> None:
        self.generator = self.generator or RuleQuestionGenerator()
        self.retriever = HybridRetriever(self.faqs)

    def health_governance(self) -> list[HealthFinding]:
        findings: list[HealthFinding] = []
        by_question: defaultdict[str, list[str]] = defaultdict(list)
        by_similar: defaultdict[str, list[str]] = defaultdict(list)
        category_counts = Counter(faq.category for faq in self.faqs)
        for faq in self.faqs:
            by_question["".join(tokenize(faq.question))].append(faq.faq_id)
            for question in faq.similar_questions:
                by_similar["".join(tokenize(question))].append(faq.faq_id)

        for ids in by_question.values():
            if len(ids) > 1:
                findings.append(HealthFinding("duplicate_faq", "high", tuple(ids), "标准问重复"))
        for ids in by_similar.values():
            if len(ids) > 1:
                findings.append(HealthFinding("conflicting_similar_question", "high", tuple(ids), "相似问指向多个 FAQ"))
        for faq in self.faqs:
            if len(faq.similar_questions) < 2:
                findings.append(HealthFinding("insufficient_coverage", "medium", (faq.faq_id,), "相似问数量不足"))
        for category, count in category_counts.items():
            if count > max(8, len(self.faqs) // 2):
                ids = tuple(faq.faq_id for faq in self.faqs if faq.category == category)
                findings.append(HealthFinding("category_overloaded", "medium", ids, f"类别 {category} 包含 {count} 条 FAQ"))
        return findings

    def badcase_strategy(self, badcases: list[Badcase]) -> list[OptimizationAction]:
        actions: list[OptimizationAction] = []
        for badcase in badcases:
            hits = self.retriever.search(badcase.query, top_k=1)
            target = badcase.expected_faq_id or (hits[0].faq_id if hits else None)
            if not target:
                continue
            actions.append(OptimizationAction(
                "add_similar_question",
                target,
                {"question": badcase.query, "reason": badcase.reason},
                risk="low",
            ))
        return actions

    def expand_questions(self) -> list[OptimizationAction]:
        actions: list[OptimizationAction] = []
        for faq in self.faqs:
            existing = {"".join(tokenize(item)) for item in faq.similar_questions}
            for question in self.generator.generate(faq):
                normalized = "".join(tokenize(question))
                if normalized and normalized not in existing:
                    actions.append(OptimizationAction(
                        "add_similar_question",
                        faq.faq_id,
                        {"question": question, "source": "rule_generator"},
                    ))
        return actions

    def run(self, badcases: list[Badcase] | None = None) -> OptimizationReport:
        health = self.health_governance()
        badcase_actions = self.badcase_strategy(badcases or [])
        expansion_actions = self.expand_questions()
        coverage_before = sum(bool(faq.similar_questions) for faq in self.faqs) / max(1, len(self.faqs))
        return OptimizationReport(
            health_findings=health,
            badcase_actions=badcase_actions,
            expansion_actions=expansion_actions,
            metrics={
                "faq_count": float(len(self.faqs)),
                "coverage_before": round(coverage_before, 3),
                "candidate_action_count": float(len(badcase_actions) + len(expansion_actions)),
            },
        )
