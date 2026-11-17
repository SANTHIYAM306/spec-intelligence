from spec_intelligence.gold import validate_gold_set


def test_gold_validator_accepts_independently_verified_real_evidence():
    records = [{"element_id": "E1", "doc_id": "pd", "revision": "R1", "page": 2,
                "text": "Grounded requirement", "synthetic": False}]
    gold = [{"id": "Q1", "question": "What is required?", "category": "S",
             "author": "member-a", "verifier": "member-b", "gold_answer": "Requirement X.",
             "gold_element_ids": ["E1"]}]
    result = validate_gold_set(gold, records, minimum_questions=1)
    assert result["valid"] is True
    assert result["independently_verified_count"] == 1


def test_gold_validator_rejects_synthetic_evidence_and_pending_verifier():
    records = [{"element_id": "SYN-1", "doc_id": "demo", "page": 1,
                "text": "synthetic", "synthetic": True}]
    gold = [{"id": "Q1", "question": "Question?", "category": "S",
             "author": "member-a", "verifier": "pending", "gold_answer": "Answer",
             "gold_element_ids": ["SYN-1"]}]
    result = validate_gold_set(gold, records, minimum_questions=1)
    assert result["valid"] is False
    codes = {e["code"] for e in result["errors"]}
    assert "not_independently_verified" in codes
    assert "invalid_evidence_references" in codes


def test_gold_validator_requires_explicit_reason_for_unanswerable_item():
    gold = [{"id": "Q1", "question": "Out of scope?", "category": "unanswerable",
             "author": "member-a", "verifier": "member-b", "gold_answer": "Not in corpus; decline.",
             "gold_element_ids": []}]
    assert validate_gold_set(gold, [], minimum_questions=1)["valid"] is True
