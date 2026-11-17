from spec_intelligence.chunking import chunk_elements
from spec_intelligence.figures import validate_figure_json, make_figure_element
from spec_intelligence.metrics import evaluate_rankings, ndcg_at_k

def test_chunking_preserves_parent_and_metadata():
    rows = chunk_elements([{"element_id":"p1","doc_id":"D","page":2,"text":"A "*1000,"element_type":"paragraph"}], max_chars=200, overlap=20)
    assert len(rows) > 1
    assert all(r["parent_id"] == "p1" and r["page"] == 2 for r in rows)
    assert all(len(r["text"]) <= 200 for r in rows)

def test_tables_remain_atomic():
    text = "x" * 300
    rows = chunk_elements([{"element_id":"t1","text":text,"element_type":"table"}], max_chars=100, overlap=10)
    assert len(rows) == 1 and rows[0]["text"] == text

def test_state_machine_schema_validation():
    good = {"figure_type":"state_machine","description":"Two states","entities":["A","B"],
            "states":["A","B"],"transitions":[{"from":"A","to":"B","trigger":"event"}]}
    assert validate_figure_json(good) == (True, [])
    bad = {"figure_type":"state_machine","description":"Bad","states":[],"transitions":[{"from":"A"}]}
    valid, errors = validate_figure_json(bad)
    assert not valid and errors

def test_metrics_report_expected_ranking():
    assert ndcg_at_k(["x","gold"], {"gold"}, 5) > 0
    out = evaluate_rankings([{"ranked_ids":["x","gold"],"gold_ids":["gold"]}], k=5)
    assert out["mrr"] == 0.5
