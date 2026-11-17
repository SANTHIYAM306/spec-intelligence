"""Reproducible A--F ablation runner with explicit dependency gates.

Configurations are only labelled ``ran`` when their defining components actually ran.
The reference A--F sequence is cumulative, so E and F are blocked when D is blocked;
standalone graph/agent diagnostics are reported separately and are never passed off as
valid full-system ablations.
"""
from __future__ import annotations
from typing import Any
from .agent import run_agent
from .evaluation import evaluate_gold


def _agent_diagnostics(records: list[dict[str, Any]], gold: list[dict[str, Any]], k: int) -> list[dict[str, Any]]:
    rows = []
    for item in gold:
        result = run_agent(item["question"], records, k=k, retrieval_mode="lexical")
        expected = set(item.get("gold_element_ids", []))
        cited = {e.get("element_id") for e in result.get("evidence", [])}
        rows.append({
            "id": item.get("id"),
            "category": item.get("category", "unspecified"),
            "declined": result.get("declined", True),
            "gold_evidence_in_answer": bool(expected & cited),
            "retrieved_evidence_ids": [e.get("element_id") for e in result.get("evidence", [])],
            "trace": result.get("trace", []),
        })
    return rows


def run_ablation_suite(records: list[dict[str, Any]], gold: list[dict[str, Any]],
                       page_index: list[dict[str, Any]] | None = None, k: int = 5) -> dict[str, Any]:
    """Run available configs and report unavailable cumulative configs without fabricating scores."""
    if not gold:
        raise ValueError("The ablation suite requires a non-empty, manually verified gold set")
    configs: dict[str, dict[str, Any]] = {}

    # A: naive dense RAG. Do not silently replace dense retrieval with lexical retrieval.
    try:
        configs["A"] = {
            "status": "ran",
            "description": "Naive dense retrieval over extracted text",
            "metrics": evaluate_gold(records, gold, k=k, retrieval_mode="dense"),
        }
    except (RuntimeError, ImportError) as exc:
        configs["A"] = {"status": "blocked", "description": "Naive dense RAG over extracted text",
                        "reason": str(exc)}

    # B: hybrid BM25+dense plus cross-encoder reranking.
    try:
        configs["B"] = {
            "status": "ran",
            "description": "A + hybrid BM25/dense retrieval + cross-encoder reranker",
            "metrics": evaluate_gold(records, gold, k=k, retrieval_mode="hybrid", rerank=True),
        }
    except (RuntimeError, ImportError) as exc:
        configs["B"] = {"status": "blocked", "description": "Hybrid retrieval + reranker",
                        "reason": str(exc)}

    # C and D require actual indexed page-image model outputs; presence of a manifest alone
    # is not sufficient evidence that the vision model ran successfully.
    configs["C"] = {"status": "blocked", "description": "Vision-only ColQwen/ColPali page retrieval",
                    "reason": "A validated page-image index with model scores and page-level gold labels is required.",
                    "page_index_supplied": bool(page_index)}
    configs["D"] = {"status": "blocked", "description": "B + C fused, with structured tables and figures",
                    "reason": "Depends on a measured C run plus verified structured table/figure extraction."}

    # E/F are cumulative and cannot be scored as the assignment defines them unless D exists.
    configs["E"] = {"status": "blocked", "description": "D + knowledge-graph tool",
                    "reason": "Configuration D is blocked; standalone graph diagnostics are reported separately."}
    configs["F"] = {"status": "blocked", "description": "E + planning, reflection and citation verification",
                    "reason": "Configuration E is blocked; standalone agent diagnostics are reported separately."}

    diagnostics = _agent_diagnostics(records, gold, k)
    return {
        "scope": "current local corpus only",
        "gold_question_count": len(gold),
        "gold_set_verified_by_runner": False,
        "configurations": configs,
        "diagnostics_not_comparable_to_A_F": {
            "status": "ran",
            "description": "Standalone deterministic agent workflow using lexical retrieval and candidate graph",
            "questions": diagnostics,
            "warning": "Diagnostic traces are not a valid F ablation or evidence of real-spec accuracy.",
        },
        "warning": "Use the same independently verified gold set for all comparable configurations. Do not report blocked configurations as results.",
    }
