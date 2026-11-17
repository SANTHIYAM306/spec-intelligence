from spec_intelligence.agent import run_agent, plan_question
from spec_intelligence.corpus import DEMO_RECORDS

def test_plan_classifies_cross_document_question():
    assert plan_question("Compare X versus Y")["question_type"] == "comparison"

def test_agent_trace_and_decline():
    result = run_agent("What is the quantum banana protocol?", DEMO_RECORDS, retrieval_mode="lexical")
    assert result["declined"]
    assert [x["action"] for x in result["trace"]][-1] == "citation_verifier"
    assert [x["action"] for x in result["trace"]][0] == "plan"
    assert result["limits"]["steps_used"] <= result["limits"]["max_steps"]

def test_agent_respects_small_step_budget():
    result = run_agent("Which test verifies R-100?", DEMO_RECORDS, max_steps=1, retrieval_mode="lexical")
    assert result["declined"]
    assert result["limits"]["steps_used"] == 1
