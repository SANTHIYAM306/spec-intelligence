from spec_intelligence.corpus import DEMO_RECORDS
from spec_intelligence.graph import build_graph, graph_path

def test_graph_path_returns_source_provenance():
    graph = build_graph(DEMO_RECORDS)
    path = graph_path(graph, "R-100", "SYNTHETIC-PD-SPEC::section::4.1", max_depth=2)
    assert path["found"]
    assert path["edges"]
    assert path["edges"][0]["provenance"]["element_id"]

def test_graph_path_missing_entity_is_explicit():
    result = graph_path(build_graph(DEMO_RECORDS), "MISSING_SOURCE", "MISSING_TARGET")
    assert not result["found"]
    assert result["reason"] == "source_or_target_entity_not_found"
