from spec_intelligence.tables import stitch_table_continuations
from spec_intelligence.chunking import chunk_elements

def test_stitches_matching_adjacent_table_headers_and_keeps_provenance():
    records = [
      {"element_id":"D-p4-t1","doc_id":"D","revision":"R1","page":4,"element_type":"table",
       "table_json":[["Name","Value"],["A","1"]],"text":"| Name | Value |"},
      {"element_id":"D-p5-t1","doc_id":"D","revision":"R1","page":5,"element_type":"table",
       "table_json":[["Name","Value"],["B","2"]],"text":"| Name | Value |"},
    ]
    out = stitch_table_continuations(records)
    assert len(out) == 1
    assert out[0]["source_element_ids"] == ["D-p4-t1","D-p5-t1"]
    assert out[0]["table_json"] == [["Name","Value"],["A","1"],["B","2"]]
    assert out[0]["page_end"] == 5

def test_does_not_stitch_across_revisions():
    records = [
      {"element_id":"a","doc_id":"D","revision":"R1","page":4,"element_type":"table","table_json":[["A"],["1"]]},
      {"element_id":"b","doc_id":"D","revision":"R2","page":5,"element_type":"table","table_json":[["A"],["2"]]},
    ]
    assert stitch_table_continuations(records) == []

def test_stitched_tables_remain_atomic():
    rows = chunk_elements([{"element_id":"st","element_type":"stitched_table","text":"x"*300}], max_chars=100, overlap=10)
    assert len(rows) == 1
