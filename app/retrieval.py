from __future__ import annotations

import math
import re
import hashlib
from collections import Counter, defaultdict
from dataclasses import dataclass

from .models import FAQ, RetrievalHit


def tokenize(text: str) -> list[str]:
    normalized = text.casefold()
    words = re.findall(r"[a-z0-9_]+", normalized)
    cjk = re.findall(r"[\u4e00-\u9fff]", normalized)
    bigrams = [normalized[i : i + 2] for i in range(len(normalized) - 1)
               if all("\u4e00" <= char <= "\u9fff" for char in normalized[i : i + 2])]
    return words + cjk + bigrams


class BM25Retriever:
    def __init__(self, faqs: list[FAQ]) -> None:
        self.faqs = faqs
        self.tokens = [tokenize(" ".join((faq.question, *faq.similar_questions))) for faq in faqs]
        self.counts = [Counter(item) for item in self.tokens]
        self.document_frequency = Counter(term for item in self.tokens for term in set(item))
        self.avg_length = sum(map(len, self.tokens)) / max(1, len(self.tokens))

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        terms = tokenize(query)
        scores: list[tuple[str, float]] = []
        total = len(self.faqs)
        for faq, counts, tokens in zip(self.faqs, self.counts, self.tokens):
            score = 0.0
            for term in terms:
                frequency = counts.get(term, 0)
                if not frequency:
                    continue
                df = self.document_frequency.get(term, 0)
                inverse_frequency = math.log(1 + (total - df + 0.5) / (df + 0.5))
                normalization = frequency + 1.5 * (1 - 0.75 + 0.75 * len(tokens) / max(1, self.avg_length))
                score += inverse_frequency * frequency * 2.5 / normalization
            if score:
                scores.append((faq.faq_id, score))
        return sorted(scores, key=lambda item: (-item[1], item[0]))[:top_k]


def _hash_vector(text: str, dimension: int = 96) -> list[float]:
    values = [0.0] * dimension
    for index, term in enumerate(tokenize(text)):
        digest = hashlib.blake2b(term.encode("utf-8"), digest_size=4).digest()
        bucket = int.from_bytes(digest, "big") % dimension
        values[bucket] += 1.0 + (index % 3) * 0.1
    norm = math.sqrt(sum(value * value for value in values)) or 1.0
    return [value / norm for value in values]


class DenseRetriever:
    def __init__(self, faqs: list[FAQ]) -> None:
        self.faqs = faqs
        self.vectors = [_hash_vector(" ".join((faq.question, *faq.similar_questions))) for faq in faqs]

    def search(self, query: str, top_k: int = 5) -> list[tuple[str, float]]:
        query_vector = _hash_vector(query)
        scored = []
        for faq, vector in zip(self.faqs, self.vectors):
            scored.append((faq.faq_id, sum(a * b for a, b in zip(query_vector, vector))))
        return sorted(scored, key=lambda item: (-item[1], item[0]))[:top_k]


@dataclass
class HybridRetriever:
    faqs: list[FAQ]
    bm25_weight: float = 0.6
    dense_weight: float = 1.0
    rrf_k: int = 60

    def __post_init__(self) -> None:
        self.bm25 = BM25Retriever(self.faqs)
        self.dense = DenseRetriever(self.faqs)
        self.by_id = {faq.faq_id: faq for faq in self.faqs}

    def search(self, query: str, top_k: int = 5) -> list[RetrievalHit]:
        depth = max(top_k * 2, 8)
        channels = {
            "bm25": self.bm25.search(query, depth),
            "dense": self.dense.search(query, depth),
        }
        fused: defaultdict[str, float] = defaultdict(float)
        evidence: defaultdict[str, set[str]] = defaultdict(set)
        for channel, hits in channels.items():
            weight = self.bm25_weight if channel == "bm25" else self.dense_weight
            for rank, (faq_id, score) in enumerate(hits, start=1):
                fused[faq_id] += weight / (self.rrf_k + rank)
                evidence[faq_id].add(channel)

        results: list[RetrievalHit] = []
        query_terms = set(tokenize(query))
        for faq_id in sorted(fused, key=lambda item: (-fused[item], item)):
            faq = self.by_id[faq_id]
            lexical_overlap = len(query_terms & set(tokenize(faq.question)))
            rerank_score = fused[faq_id] + min(0.05, lexical_overlap * 0.01)
            results.append(RetrievalHit(faq_id, faq.question, faq.category, rerank_score, tuple(sorted(evidence[faq_id]))))
        return results[:top_k]
