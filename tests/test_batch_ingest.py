import json
from pathlib import Path
import pytest
from spec_intelligence import batch_ingest


def test_batch_ingest_skips_macos_stubs_and_reports_duplicate_content(tmp_path, monkeypatch):
    root = tmp_path / "corpus"
    (root / "pd").mkdir(parents=True)
    (root / "__MACOSX").mkdir()
    (root / "pd" / "main.pdf").write_bytes(b"same-pdf")
    (root / "pd" / "copy.pdf").write_bytes(b"same-pdf")
    (root / "pd" / "._main.pdf").write_bytes(b"stub")
    (root / "__MACOSX" / "ignored.pdf").write_bytes(b"stub")

    def fake_ingest(pdf, output, **kwargs):
        Path(output).write_text("scratch", encoding="utf-8")
        return [{"element_id": f"{kwargs['doc_id']}-P1-B1", "doc_id": kwargs['doc_id'],
                 "revision": kwargs['revision'], "page": 1, "text": "fixture", "synthetic": False}]

    monkeypatch.setattr(batch_ingest, "ingest_pdf", fake_ingest)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({
        "pd/main.pdf": {"doc_id": "pd_main", "revision": "R1"},
        "pd/copy.pdf": {"doc_id": "pd_copy", "revision": "R1"},
    }), encoding="utf-8")
    output, report_path = tmp_path / "elements.jsonl", tmp_path / "report.json"
    report = batch_ingest.ingest_directory(root, output, report_path, manifest)
    assert report["pdf_count_found"] == 2
    assert report["pdf_count_ingested"] == 2
    assert report["pdf_count_failed"] == 0
    assert report["duplicate_content_groups"] == [["pd/copy.pdf", "pd/main.pdf"]]
    assert len(output.read_text(encoding="utf-8").splitlines()) == 2
    assert json.loads(report_path.read_text(encoding="utf-8"))["element_count"] == 2


def test_batch_ingest_rejects_duplicate_ids_from_manifest(tmp_path, monkeypatch):
    root = tmp_path / "corpus"
    root.mkdir()
    (root / "a.pdf").write_bytes(b"a")
    (root / "b.pdf").write_bytes(b"b")

    def fake_ingest(pdf, output, **kwargs):
        return [{"element_id": "same-id", "doc_id": kwargs['doc_id'], "page": 1, "text": "x"}]

    monkeypatch.setattr(batch_ingest, "ingest_pdf", fake_ingest)
    manifest = tmp_path / "manifest.json"
    manifest.write_text(json.dumps({"a.pdf": {"doc_id": "same"}, "b.pdf": {"doc_id": "same"}}), encoding="utf-8")
    with pytest.raises(ValueError, match="Duplicate element IDs"):
        batch_ingest.ingest_directory(root, tmp_path / "elements.jsonl", manifest_path=manifest)
