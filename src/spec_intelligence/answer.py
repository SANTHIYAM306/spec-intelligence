"""Conservative answer generation from retrieved evidence."""
from __future__ import annotations

from typing import Any

INSUFFICIENT = (
    "I could not find sufficient evidence in the indexed corpus to answer this question. "
    "No technical value should be inferred from this result."
)


def format_citation(record: dict[str, Any]) -> str:
    return (
        f"[{record.get('doc_id', 'unknown-doc')}, "
        f"rev. {record.get('revision', 'unknown')}, "
        f"§{record.get('section', 'unknown-section')}, "
        f"p. {record.get('page', 'unknown-page')}, "
        f"{record.get('element_id', 'unknown-element')}"
        + (f", region={record.get('bbox')}" if record.get("bbox") else "")
        + (f", type={record.get('element_type')}" if record.get("element_type") else "") + "]"
    )


def answer_question(question: str, retrieved: list[dict[str, Any]], min_score: float = 0.2) -> dict[str, Any]:
    """Return evidence excerpts with citations, or decline on insufficient retrieval."""
    usable = []
    for item in retrieved:
        mode = item.get("retrieval_mode", "lexical")
        threshold = 0.01 if mode == "hybrid" else min_score
        if float(item.get("score", 0)) >= threshold:
            usable.append(item)
    if not usable:
        return {"answer": INSUFFICIENT, "citations": [], "declined": True, "evidence": []}
    evidence = []
    citations = []
    for item in usable[:3]:
        evidence.append({
            "text": str(item.get("text", "")),
            "citation": format_citation(item),
            "score": item.get("score"),
            "element_id": item.get("element_id"),
        })
        citations.append(format_citation(item))
    # This baseline deliberately does not invent a synthesis or technical values.
    excerpts = "\n".join(f"- {item['text']} {item['citation']}" for item in evidence)
    answer = (
        "Relevant retrieved evidence (baseline mode; verify the source before using it):\n"
        + excerpts
    )
    return {"answer": answer, "citations": citations, "declined": False, "evidence": evidence}
