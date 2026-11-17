from pathlib import Path
import pytest
from spec_intelligence.ingest import ingest_pdf, _table_markdown

def test_non_pdf_input_is_rejected(tmp_path: Path):
    source = tmp_path / "not-a-pdf.txt"
    source.write_text("hello", encoding="utf-8")
    with pytest.raises(ValueError):
        ingest_pdf(source, tmp_path / "out.jsonl")

def test_table_markdown_pads_short_rows():
    result = _table_markdown([["Name", "Value"], ["A", "1"], ["B"]])
    assert "| B |  |" in result
    assert "---" in result
