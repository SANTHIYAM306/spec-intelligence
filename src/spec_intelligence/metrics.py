"""Transparent retrieval and grounding metrics; no LLM judge is assumed."""
from __future__ import annotations
import math
from typing import Any

def recall_at_k(ranked_ids: list[str], gold_ids: set[str], k: int = 5) -> float:
    if not gold_ids: return 1.0 if not ranked_ids[:k] else 0.0
    return len(set(ranked_ids[:k]) & gold_ids) / len(gold_ids)

def reciprocal_rank(ranked_ids: list[str], gold_ids: set[str]) -> float:
    for i, item in enumerate(ranked_ids, 1):
        if item in gold_ids: return 1.0 / i
    return 0.0

def ndcg_at_k(ranked_ids: list[str], gold_ids: set[str], k: int = 5) -> float:
    dcg = sum((1 / math.log2(i+2)) for i, item in enumerate(ranked_ids[:k]) if item in gold_ids)
    ideal_n = min(len(gold_ids), k)
    ideal = sum(1 / math.log2(i+2) for i in range(ideal_n))
    return dcg / ideal if ideal else 0.0

def evaluate_rankings(rows: list[dict[str, Any]], k: int = 5) -> dict[str, Any]:
    if not rows: return {"questions": 0, "recall_at_k": 0.0, "mrr": 0.0, "ndcg_at_k": 0.0}
    recalls, rrs, ndcgs = [], [], []
    for row in rows:
        ranked = list(row.get("ranked_ids", [])); gold = set(row.get("gold_ids", []))
        recalls.append(recall_at_k(ranked, gold, k)); rrs.append(reciprocal_rank(ranked, gold))
        ndcgs.append(ndcg_at_k(ranked, gold, k))
    return {"questions": len(rows), "k": k, "recall_at_k": round(sum(recalls)/len(rows), 4),
            "mrr": round(sum(rrs)/len(rows), 4), "ndcg_at_k": round(sum(ndcgs)/len(rows), 4)}
