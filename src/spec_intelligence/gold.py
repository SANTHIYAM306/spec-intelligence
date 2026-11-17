"""Gold-set schema and evidence validation for the assignment evaluation harness."""
from __future__ import annotations
from collections import Counter
from typing import Any

PENDING_MARKERS = {"", "pending", "unverified", "unknown", "template", "tbd", "n/a"}


def _evidence_ids(item: dict[str, Any]) -> list[str]:
    ids = item.get("gold_element_ids")
    if isinstance(ids, list):
        return [str(x) for x in ids if str(x).strip()]
    evidence = item.get("gold_evidence", [])
    if isinstance(evidence, list):
        return [str(x["element_id"]) for x in evidence
                if isinstance(x, dict) and x.get("element_id")]
    return []


def validate_gold_set(gold: list[dict[str, Any]], records: list[dict[str, Any]],
                      minimum_questions: int = 60) -> dict[str, Any]:
    """Validate gold-set completeness and source-evidence references without judging truth.

    A structurally valid item is not automatically factually correct: the named verifier must
    still check the answer against the licensed source PDF. Unanswerable questions should use
    an empty evidence list and include an explicit reason in ``gold_answer``.
    """
    element_by_id = {str(r.get("element_id")): r for r in records if r.get("element_id")}
    errors: list[dict[str, Any]] = []
    warnings: list[str] = []
    ids = [str(x.get("id", "")).strip() for x in gold]
    duplicates = sorted(x for x, n in Counter(ids).items() if x and n > 1)
    if len(gold) < minimum_questions:
        errors.append({"code": "too_few_questions", "message": f"Found {len(gold)}; require at least {minimum_questions}."})
    if duplicates:
        errors.append({"code": "duplicate_ids", "ids": duplicates})
    questions = [str(x.get("question", "")).strip().casefold() for x in gold if str(x.get("question", "")).strip()]
    dup_questions = sorted(q for q, n in Counter(questions).items() if n > 1)
    if dup_questions:
        errors.append({"code": "duplicate_questions", "questions": dup_questions})
    verified_count = 0
    unanswerable_count = 0
    missing_evidence = []
    for index, item in enumerate(gold, 1):
        label = str(item.get("id") or f"row-{index}")
        question = str(item.get("question", "")).strip()
        category = str(item.get("category", "")).strip()
        answer = str(item.get("gold_answer", "")).strip()
        author = str(item.get("author", "")).strip().casefold()
        verifier = str(item.get("verifier", "")).strip().casefold()
        evidence_ids = _evidence_ids(item)
        is_unanswerable = category.casefold() in {"u", "unanswerable", "out_of_corpus", "false_premise"} or bool(item.get("unanswerable"))
        if not question: errors.append({"code": "missing_question", "id": label})
        if not category: errors.append({"code": "missing_category", "id": label})
        if not answer: errors.append({"code": "missing_gold_answer", "id": label})
        if author in PENDING_MARKERS: errors.append({"code": "missing_author", "id": label})
        verified = verifier not in PENDING_MARKERS and verifier != author
        if not verified:
            errors.append({"code": "not_independently_verified", "id": label, "verifier": verifier or None})
        else:
            verified_count += 1
        if is_unanswerable:
            unanswerable_count += 1
            if evidence_ids:
                errors.append({"code": "unanswerable_has_gold_evidence", "id": label, "element_ids": evidence_ids})
        elif not evidence_ids:
            errors.append({"code": "missing_gold_evidence", "id": label})
        for element_id in evidence_ids:
            record = element_by_id.get(element_id)
            if record is None:
                missing_evidence.append({"id": label, "element_id": element_id, "problem": "not_found_in_corpus"})
            elif record.get("synthetic"):
                missing_evidence.append({"id": label, "element_id": element_id, "problem": "synthetic_fixture_not_real_evidence"})
            elif not record.get("doc_id") or not record.get("page"):
                missing_evidence.append({"id": label, "element_id": element_id, "problem": "missing_document_or_page_provenance"})
    if missing_evidence:
        errors.append({"code": "invalid_evidence_references", "items": missing_evidence})
    if len(records) == 0:
        warnings.append("No corpus records supplied; evidence membership could not be checked.")
    return {
        "valid": not errors,
        "question_count": len(gold),
        "minimum_questions": minimum_questions,
        "independently_verified_count": verified_count,
        "unanswerable_count": unanswerable_count,
        "corpus_element_count": len(records),
        "error_count": len(errors), "errors": errors, "warnings": warnings,
        "note": "Structural validation does not prove the gold answer is factually correct; a second reviewer must inspect each cited PDF page."
    }
