from spec_intelligence.ablation import run_ablation_suite
from spec_intelligence.corpus import DEMO_RECORDS


def test_ablation_report_never_claims_vision_or_cumulative_runs_without_evidence():
    gold = [{"id": "q1", "question": "Which test verifies requirement R-100?",
             "gold_element_ids": ["SYN-002"], "category": "single_hop"}]
    report = run_ablation_suite(DEMO_RECORDS, gold, k=3)
    assert report["gold_question_count"] == 1
    assert report["configurations"]["C"]["status"] == "blocked"
    assert report["configurations"]["D"]["status"] == "blocked"
    assert report["configurations"]["E"]["status"] == "blocked"
    assert report["configurations"]["F"]["status"] == "blocked"
    assert report["diagnostics_not_comparable_to_A_F"]["status"] == "ran"
