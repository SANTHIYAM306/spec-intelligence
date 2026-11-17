from spec_intelligence.answer import answer_question
from spec_intelligence.corpus import DEMO_RECORDS
from spec_intelligence.retrieval import search

def test_answer_includes_source_citation():
    result = answer_question("Which test verifies R-100?", search("Which test verifies R-100?", DEMO_RECORDS, mode="lexical"))
    assert not result["declined"]
    assert "SYNTHETIC-PD-TEST" in result["answer"]
    assert "p. 8" in result["answer"]

def test_unknown_question_declines():
    result = answer_question("What is the quantum banana protocol?", [])
    assert result["declined"]
    assert not result["citations"]
