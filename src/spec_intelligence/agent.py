"""Bounded plan-act-reflect agent using retrieval and graph tools; no model-memory answers."""
from __future__ import annotations
import time
from typing import Any
from .answer import answer_question
from .graph import build_graph, graph_query
from .retrieval import search

def plan_question(question: str) -> dict[str, Any]:
    q = question.lower()
    if any(w in q for w in ("compare", "difference", "versus", " vs ")): kind = "comparison"
    elif any(w in q for w in ("which test", "test case", "compliance test", "verifies")): kind = "test_lookup"
    elif any(w in q for w in ("figure", "diagram", "state machine", "timing diagram")): kind = "figure_lookup"
    elif any(w in q for w in ("not in", "outside", "does not contain", "unanswerable")): kind = "unanswerable_check"
    elif len(q.split()) > 12 or any(w in q for w in ("and where", "across", "which section", "what limit")): kind = "multi_hop"
    else: kind = "fact_lookup"
    return {"question_type": kind, "steps": ["plan", "search_text", "graph_query",
        "reflect_or_corrective_search", "citation_membership_check", "answer_or_decline"]}

def run_agent(question: str, records: list[dict[str, Any]], k: int = 6, max_steps: int = 7,
              min_score: float = 0.2, retrieval_mode: str = "hybrid",
              rerank: bool = False, llm_model: str | None = None,
              local_files_only: bool = True,
              page_index: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    """Run a deterministic bounded workflow and retain an auditable tool trace."""
    if max_steps < 1: raise ValueError("max_steps must be >= 1")
    start = time.perf_counter()
    plan = plan_question(question)
    trace: list[dict[str, Any]] = [{"step": 1, "action": "plan", "result": plan}]
    if max_steps == 1:
        return {"answer": "Execution budget ended before evidence retrieval.", "citations": [],
                "declined": True, "evidence": [], "plan": plan, "trace": trace,
                "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "limits": {"max_steps": max_steps, "steps_used": 1}}
    hits = search(question, records, k=k, mode=retrieval_mode, rerank=rerank)
    trace.append({"step": 2, "action": "search_text", "query": question, "hit_count": len(hits),
                  "retrieval_mode": hits[0].get("retrieval_mode") if hits else retrieval_mode,
                  "element_ids": [h.get("element_id") for h in hits]})
    vision_used = False
    if page_index and plan["question_type"] == "figure_lookup":
        try:
            from .vision import search_pages
            page_hits = search_pages(question, page_index, k=k)
            mapped = []
            for page_hit in page_hits:
                same_page = [r for r in records if r.get("doc_id") == page_hit.get("doc_id")
                             and int(r.get("page") or 0) == int(page_hit.get("page") or 0)]
                for rec in same_page[:3]:
                    mapped.append({**rec, "vision_score": page_hit.get("vision_score"),
                                   "retrieval_mode": "vision_page", "score": page_hit.get("vision_score", 0.0)})
            if mapped:
                from .retrieval import reciprocal_rank_fusion
                hits = reciprocal_rank_fusion(hits, mapped, k=k)
                for item in hits:
                    item.setdefault("score", item.get("rrf_score", 0.0))
                vision_used = True
            trace.append({"step": 3, "action": "search_pages", "status": "completed",
                          "page_hit_count": len(page_hits), "mapped_element_count": len(mapped)})
        except Exception as exc:
            trace.append({"step": 3, "action": "search_pages", "status": "unavailable",
                          "error_type": type(exc).__name__, "message": str(exc)[:250]})
    graph_hits = {"entities": [], "edges": []}
    if max_steps >= len(trace) + 1:
        graph = build_graph(records)
        graph_hits = graph_query(graph, question_entity_hint(question), relation=None)
        trace.append({"step": len(trace)+1, "action": "graph_query", "entity_hint": question_entity_hint(question),
                      "node_count": len(graph_hits["entities"]), "edge_count": len(graph_hits["edges"])})
    if max_steps < len(trace) + 1:
        return {"answer": "Execution budget ended before evidence reflection and citation verification; no final answer emitted.",
                "citations": [], "declined": True, "evidence": [], "plan": plan, "trace": trace,
                "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "graph_context": graph_hits, "limits": {"max_steps": max_steps, "steps_used": len(trace)}}
    # Reflection stage: if first-pass retrieval returns no evidence, try the strongest
    # protocol identifier extracted from the question as a corrective lexical query.
    fallback_used = False
    if not hits:
        hint = question_entity_hint(question)
        if hint and hint.lower() != question.lower() and max_steps >= len(trace) + 2:
            fallback = search(hint, records, k=k, mode="lexical")
            if fallback:
                hits = fallback
                fallback_used = True
    trace.append({"step": len(trace)+1, "action": "reflect_on_evidence",
                  "evidence_count": len(hits), "corrective_search_used": fallback_used,
                  "decision": "continue_to_verification" if hits else "decline_insufficient_evidence"})
    if max_steps < len(trace) + 1:
        return {"answer": "Execution budget ended before citation verification; no final answer emitted.",
                "citations": [], "declined": True, "evidence": [], "plan": plan, "trace": trace,
                "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "graph_context": graph_hits, "limits": {"max_steps": max_steps, "steps_used": len(trace)}}
    result = answer_question(question, hits, min_score=min_score)
    generation_skipped_budget = bool(llm_model and not result.get("declined") and max_steps < len(trace) + 2)
    if llm_model and not result.get("declined") and not generation_skipped_budget:
        try:
            from .generation import answer_with_local_llm
            selected_ids = {x.get("element_id") for x in result.get("evidence", [])}
            generation_evidence = [h for h in hits if h.get("element_id") in selected_ids]
            result = answer_with_local_llm(question, generation_evidence, llm_model,
                                           local_files_only=local_files_only)
            trace.append({"step": len(trace)+1, "action": "local_llm_generation", "status": "completed",
                          "generation_mode": result.get("generation_mode")})
        except Exception as exc:
            # Fail closed to the tested evidence-excerpt path; make fallback visible in trace.
            trace.append({"step": len(trace)+1, "action": "local_llm_generation", "status": "fallback",
                          "error_type": type(exc).__name__, "message": str(exc)[:300]})
    # Conservative verifier: every citation must be one of the retrieved evidence elements.
    allowed = {h.get("element_id") for h in hits}
    verified = all(e.get("element_id") in allowed for e in result.get("evidence", []))
    if not verified:
        result = {"answer": "I could not verify the answer against retrieved evidence.",
                  "citations": [], "declined": True, "evidence": []}
    if max_steps < len(trace) + 1:
        return {"answer": "Execution budget ended before citation verification; no final answer emitted.",
                "citations": [], "declined": True, "evidence": [], "plan": plan, "trace": trace,
                "latency_ms": round((time.perf_counter()-start)*1000, 2),
                "graph_context": graph_hits, "limits": {"max_steps": max_steps, "steps_used": len(trace)}}
    trace.append({"step": len(trace)+1, "action": "citation_verifier", "passed": verified,
                  "citation_count": len(result.get("citations", []))})
    result.update({"plan": plan, "trace": trace, "latency_ms": round((time.perf_counter()-start)*1000, 2),
                   "graph_context": graph_hits, "vision_used": vision_used,
                   "generation_skipped_budget": generation_skipped_budget,
                   "limits": {"max_steps": max_steps, "steps_used": len(trace)}})
    return result

def question_entity_hint(question: str) -> str:
    # Preserve protocol identifiers as graph anchors; fallback to the longest useful token.
    import re
    candidates = re.findall(r"\b(?:[A-Z]{1,8}[-_.][A-Z0-9_.-]+|t[A-Z][A-Za-z0-9_]+|[A-Z][a-z]+_[A-Za-z0-9_]+)\b", question)
    return max(candidates, key=len) if candidates else question
