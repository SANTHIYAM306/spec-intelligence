"""Gold-set evaluation utilities. Report scores only for supplied, source-verified gold data."""
from __future__ import annotations
from typing import Any
from .answer import answer_question
from .retrieval import search
from .metrics import ndcg_at_k

DEMO_QUESTIONS = [
    {"question": "Which test verifies requirement R-100?", "expected_id": "SYN-002"},
    {"question": "Where is the illustrative EXAMPLE_TIMER value described?", "expected_id": "SYN-003"},
    {"question": "What is the meaning of a quantum banana protocol?", "expected_id": None},
]

def evaluate_gold(records: list[dict[str, Any]], gold: list[dict[str, Any]], k: int = 5,
                  retrieval_mode: str = "lexical", rerank: bool = False) -> dict[str, Any]:
    total = len(gold); hits = 0; reciprocal_ranks = []; ndcgs = []; answered = 0; correct_declines = 0
    false_declines = 0; unsupported_answers = 0
    by_category: dict[str, dict[str, int]] = {}
    per_question = []
    for item in gold:
        question = item["question"]; expected = set(item.get("gold_element_ids", []))
        category = str(item.get("category", "unspecified"))
        stats = by_category.setdefault(category, {"questions": 0, "retrieval_hits": 0})
        stats["questions"] += 1
        ranked = search(question, records, k=k, mode=retrieval_mode, rerank=rerank)
        ranks = [i for i, h in enumerate(ranked, 1) if h.get("element_id") in expected]
        found = bool(ranks); hits += int(found); stats["retrieval_hits"] += int(found)
        reciprocal_ranks.append(1 / min(ranks) if ranks else 0)
        ndcgs.append(ndcg_at_k([str(h.get("element_id")) for h in ranked], expected, k))
        result = answer_question(question, ranked)
        if not expected and result["declined"]: correct_declines += 1
        if not expected and not result["declined"]: unsupported_answers += 1
        if expected and result["declined"]: false_declines += 1
        if expected and not result["declined"]: answered += 1
        per_question.append({"question_id": item.get("id"), "question": question, "retrieved_ids":
            [h.get("element_id") for h in ranked], "gold_ids": sorted(expected), "retrieval_hit": found,
            "declined": result["declined"]})
    return {"scope": "user-supplied gold set", "questions": total,
        "recall_at_k": round(hits / total, 4) if total else 0.0,
        "mrr": round(sum(reciprocal_ranks) / total, 4) if total else 0.0,
        "ndcg_at_k": round(sum(ndcgs) / total, 4) if total else 0.0,
        "correct_declines": correct_declines, "false_declines": false_declines,
        "unsupported_answers_on_unanswerable": unsupported_answers, "answered_with_evidence": answered,
        "by_category": by_category, "per_question": per_question,
        "warning": "Gold answers/evidence must be manually verified against the licensed source PDFs."}

def evaluate(records: list[dict[str, Any]]) -> dict[str, Any]:
    gold = [{"id": f"D{i}", "question": q["question"],
             "gold_element_ids": [q["expected_id"]] if q["expected_id"] else [],
             "category": "synthetic"} for i, q in enumerate(DEMO_QUESTIONS, 1)]
    result = evaluate_gold(records, gold, retrieval_mode="lexical")
    result["scope"] = "synthetic demo only"
    result["warning"] = "Synthetic fixture evaluation; not real-spec accuracy or a valid assignment benchmark."
    return result
