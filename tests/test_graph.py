from spec_intelligence.corpus import DEMO_RECORDS
from spec_intelligence.graph import build_graph, graph_query, resolve_entity

def test_graph_extracts_verification_relation_with_provenance():
    graph = build_graph(DEMO_RECORDS)
    assert any(edge["relation"] == "VERIFIES" for edge in graph["edges"])
    edge = next(edge for edge in graph["edges"] if edge["relation"] == "VERIFIES")
    assert edge["provenance"]["page"] == 8
    assert edge["provenance"]["doc_id"] == "SYNTHETIC-PD-TEST"

def test_graph_mentions_keep_provenance():
    graph = build_graph(DEMO_RECORDS)
    nodes = resolve_entity("R-100", graph)
    assert nodes
    assert nodes[0]["provenance"]
    assert graph_query(graph, "R-100")["entities"]
