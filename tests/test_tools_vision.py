import pytest
from spec_intelligence.tools import get_section, get_table, get_figure, tool_schemas
from spec_intelligence.vision import maxsim_score
from spec_intelligence.corpus import DEMO_RECORDS

def test_tools_return_provenance_and_schemas():
    assert get_section(DEMO_RECORDS, "SYNTHETIC-PD-SPEC", "4.2")
    assert get_table(DEMO_RECORDS, "SYN-003")["citation"]["page"] == 4
    assert get_figure(DEMO_RECORDS, "not-a-figure") is None
    assert {x["name"] for x in tool_schemas()} >= {"search_text", "graph_query", "get_table"}

def test_maxsim_primitive():
    np = pytest.importorskip("numpy")
    q = np.array([[1., 0.], [0., 1.]])
    p = np.array([[1., 0.], [0., 1.]])
    assert maxsim_score(q, p) == pytest.approx(2.0)
