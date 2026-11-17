from spec_intelligence.generation import build_grounded_prompt, validate_generated_payload
from spec_intelligence.corpus import DEMO_RECORDS

def test_prompt_contains_only_evidence_and_source_ids():
    prompt = build_grounded_prompt("Which test verifies R-100?", DEMO_RECORDS[:2])
    assert "SYN-001" in prompt and "SYN-002" in prompt
    assert "Do not use prior knowledge" in prompt

def test_generated_claims_must_cite_retrieved_elements():
    payload = {"decline": False, "reason": "", "claims":[{"text":"Evidence-backed claim", "element_ids":["SYN-002"]}]}
    assert validate_generated_payload(payload, DEMO_RECORDS[:2]) == (True, [])
    payload["claims"][0]["element_ids"] = ["NOT-RETRIEVED"]
    valid, errors = validate_generated_payload(payload, DEMO_RECORDS[:2])
    assert not valid and any("unknown element_id" in x for x in errors)

def test_decline_payload_has_no_claims():
    payload = {"decline": True, "reason":"No evidence", "claims":[]}
    assert validate_generated_payload(payload, []) == (True, [])
