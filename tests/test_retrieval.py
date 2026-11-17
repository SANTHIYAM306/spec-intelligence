from spec_intelligence.corpus import DEMO_RECORDS
from spec_intelligence.retrieval import lexical_search, reciprocal_rank_fusion, search, tokenize

def test_tokenize_keeps_technical_identifiers():
    assert "test-100" in tokenize("TEST-100 verifies R-100")

def test_search_finds_test_for_requirement():
    results = search("Which test verifies requirement R-100?", DEMO_RECORDS)
    assert results
    assert results[0]["element_id"] == "SYN-002"

def test_search_empty_query():
    assert search("!!!", DEMO_RECORDS) == []

def test_rrf_deduplicates_and_rewards_consistent_rank():
    a = [{"element_id":"x","text":"a"},{"element_id":"y","text":"b"}]
    b = [{"element_id":"x","text":"a"},{"element_id":"z","text":"c"}]
    out = reciprocal_rank_fusion(a,b,k=3)
    assert out[0]["element_id"] == "x"
    assert len({x["element_id"] for x in out}) == 3

def test_lexical_mode_is_explicit():
    out = search("R-100", DEMO_RECORDS, mode="lexical")
    assert out and out[0]["retrieval_mode"] == "lexical"
