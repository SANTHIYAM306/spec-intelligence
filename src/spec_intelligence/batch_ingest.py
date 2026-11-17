"""Batch ingestion of locally authorised PDFs with per-file error reporting.

The pipeline never extracts ZIP archives automatically and never downloads licensed
specifications. Users must accept the source licence and extract PDFs locally first.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import Counter
import tempfile
from pathlib import Path
from typing import Any
from .corpus import write_jsonl
from .ingest import ingest_pdf


def _slug(value: str) -> str:
    value = re.sub(r"[^A-Za-z0-9._-]+", "_", value.strip())
    return value.strip("._-") or "document"


def ingest_directory(root: str | Path, output: str | Path,
                     report_path: str | Path | None = None,
                     manifest_path: str | Path | None = None,
                     include_tables: bool = True,
                     render_pages_dir: str | Path | None = None) -> dict[str, Any]:
    """Recursively ingest PDFs; skip AppleDouble stubs, preserve unique IDs, continue on errors.

    Optional manifest JSON maps relative PDF paths to metadata, e.g.
    {"usb-pd/USB_PD_R3.2.pdf": {"doc_id":"usb_pd_base", "revision":"R3.2 V1.2"}}.
    Unmapped files use a stable slug of their relative path and revision ``unknown``.
    """
    source_root = Path(root).expanduser().resolve()
    if not source_root.is_dir():
        raise ValueError(f"PDF corpus directory does not exist: {source_root}")
    manifest: dict[str, Any] = {}
    if manifest_path:
        manifest_file = Path(manifest_path)
        manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
        if not isinstance(manifest, dict):
            raise ValueError("Manifest must be a JSON object keyed by relative PDF path")
    pdfs = sorted(p for p in source_root.rglob("*.pdf")
                  if p.is_file() and not p.name.startswith("._") and "__MACOSX" not in p.parts)
    records: list[dict[str, Any]] = []
    files: list[dict[str, Any]] = []
    seen_hashes: dict[str, list[str]] = {}
    failures = []
    with tempfile.TemporaryDirectory(prefix="specqa-batch-") as temp_dir:
        for pdf in pdfs:
          relative = pdf.relative_to(source_root).as_posix()
          try:
              digest = hashlib.sha256(pdf.read_bytes()).hexdigest()
              seen_hashes.setdefault(digest, []).append(relative)
              cfg = manifest.get(relative, {}) or {}
              doc_id = str(cfg.get("doc_id") or _slug(Path(relative).with_suffix("").as_posix()))
              revision = str(cfg.get("revision", "unknown"))
              image_dir = Path(render_pages_dir) / _slug(Path(relative).with_suffix("").as_posix()) if render_pages_dir else None
              tmp = Path(temp_dir) / f"{len(files):06d}-{_slug(doc_id)}.jsonl"
              extracted = ingest_pdf(pdf, tmp,
                                     include_tables=include_tables, render_pages_to=image_dir,
                                     revision=revision, doc_id=doc_id)
              # The per-file scratch JSONL lives only inside the temporary directory.
              for element in extracted:
                  element["source_relative_path"] = relative
              records.extend(extracted)
              files.append({"path": relative, "doc_id": doc_id, "revision": revision,
                            "sha256": digest, "pages": max((int(x.get("page") or 0) for x in extracted), default=0),
                            "elements": len(extracted), "status": "ingested"})
          except Exception as exc:  # one malformed PDF must not prevent the rest of the corpus
              failures.append({"path": relative, "error_type": type(exc).__name__, "error": str(exc)[:500]})
              files.append({"path": relative, "status": "failed", "error_type": type(exc).__name__})
    # Guard against accidental ID collisions from duplicate stems or a careless manifest.
    id_counts = Counter(str(x.get("element_id")) for x in records)
    duplicate_ids = sorted(x for x, count in id_counts.items() if count > 1)
    write_jsonl(records, output)
    duplicates = [paths for paths in seen_hashes.values() if len(paths) > 1]
    report = {
        "corpus_root": str(source_root), "pdf_count_found": len(pdfs),
        "pdf_count_ingested": sum(x.get("status") == "ingested" for x in files),
        "pdf_count_failed": len(failures), "element_count": len(records),
        "page_count_sum": sum(int(x.get("pages") or 0) for x in files if x.get("status") == "ingested"),
        "duplicate_content_groups": duplicates, "duplicate_element_ids": duplicate_ids,
        "files": files, "failures": failures, "elements_jsonl": str(output),
        "warnings": ["Exact-content duplicate PDFs are reported, not silently removed.",
                     "Section detection and extracted tables require source-level validation.",
                     "Raster-only pages need a separately configured OCR path."]
    }
    if report_path:
        dest = Path(report_path); dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
    if duplicate_ids:
        raise ValueError(f"Duplicate element IDs detected: {duplicate_ids[:10]}; check manifest doc_id values")
    return report
