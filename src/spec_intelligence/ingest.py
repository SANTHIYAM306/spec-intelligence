"""PDF ingestion preserving page, block, table, and bounding-box provenance.

PyMuPDF is the baseline parser. Tables are extracted when supported by the installed
PyMuPDF version. OCR and VLM are separate optional stages; empty-text pages are recorded
as OCR-needed rather than silently dropped.
"""
from __future__ import annotations
import hashlib, json, re
from pathlib import Path
from typing import Any
from .corpus import write_jsonl

def _section_hint(text: str) -> tuple[str, str]:
    for line in text.splitlines()[:12]:
        line = line.strip()
        m = re.match(r"^(\d+(?:\.\d+){0,6})\s+(.{3,120})$", line)
        if m: return m.group(1), m.group(2)
    return "unknown", "unknown"

def ingest_pdf(path: str | Path, output: str | Path, include_tables: bool = True,
               render_pages_to: str | Path | None = None, ocr_empty_pages: bool = False,
               revision: str = "unknown", doc_id: str | None = None) -> list[dict[str, Any]]:
    """Extract selectable text blocks and tables; optionally render page images for vision/OCR."""
    try: import fitz
    except ImportError as exc:
        raise RuntimeError('PDF ingestion requires: pip install -e ".[pdf]"') from exc
    pdf_path = Path(path)
    if not pdf_path.is_file() or pdf_path.suffix.lower() != ".pdf":
        raise ValueError(f"Expected an existing PDF file, got: {pdf_path}")
    digest = hashlib.sha256(pdf_path.read_bytes()).hexdigest()
    canonical_doc_id = doc_id or pdf_path.stem
    records: list[dict[str, Any]] = []
    image_dir = Path(render_pages_to) if render_pages_to else None
    if image_dir: image_dir.mkdir(parents=True, exist_ok=True)
    with fitz.open(pdf_path) as doc:
        for pidx, page in enumerate(doc):
            page_no = pidx + 1
            page_text = page.get_text("text").strip()
            section, section_title = _section_hint(page_text)
            blocks = page.get_text("blocks")
            block_count = 0
            for bidx, block in enumerate(blocks):
                text = str(block[4]).strip() if len(block) > 4 else ""
                if not text: continue
                block_count += 1
                bbox = [round(float(v), 2) for v in block[:4]]
                records.append({
                    "element_id": f"{canonical_doc_id}-P{page_no}-B{bidx+1}",
                    "doc_id": canonical_doc_id, "revision": revision,
                    "section_number": section, "section": section,
                    "section_title": section_title, "page": page_no,
                    "bbox": bbox, "element_type": "paragraph",
                    "text": text, "extractor": "pymupdf_blocks",
                    "sha256": digest, "synthetic": False
                })
            if include_tables and hasattr(page, "find_tables"):
                try:
                    for tidx, table in enumerate(page.find_tables().tables):
                        matrix = table.extract()
                        if not matrix: continue
                        safe = [[("" if cell is None else str(cell).strip()) for cell in row] for row in matrix]
                        markdown = _table_markdown(safe)
                        records.append({
                            "element_id": f"{canonical_doc_id}-P{page_no}-T{tidx+1}",
                            "doc_id": canonical_doc_id, "revision": revision,
                            "section_number": section, "section": section,
                            "section_title": section_title, "page": page_no,
                            "bbox": [round(float(v), 2) for v in table.bbox],
                            "element_type": "table", "table_json": safe,
                            "text": markdown, "markdown": markdown,
                            "extractor": "pymupdf_find_tables",
                            "sha256": digest, "synthetic": False
                        })
                except Exception as exc:
                    records.append({
                        "element_id": f"{canonical_doc_id}-P{page_no}-TABLE-ERROR",
                        "doc_id": canonical_doc_id, "revision": revision,
                        "section_number": section, "section": section, "page": page_no,
                        "element_type": "parser_warning", "text": f"Table extraction failed: {type(exc).__name__}",
                        "extractor": "pymupdf_find_tables", "synthetic": False
                    })
            if not page_text and ocr_empty_pages:
                try:
                    import pytesseract
                    from PIL import Image
                    import io
                    pix = page.get_pixmap(matrix=fitz.Matrix(2, 2), alpha=False)
                    ocr_text = pytesseract.image_to_string(Image.open(io.BytesIO(pix.tobytes("png")))).strip()
                    if ocr_text:
                        records.append({
                            "element_id": f"{canonical_doc_id}-P{page_no}-OCR",
                            "doc_id": canonical_doc_id, "revision": revision,
                            "section_number": section, "section": section,
                            "section_title": section_title, "page": page_no,
                            "bbox": None, "element_type": "ocr_text", "text": ocr_text,
                            "extractor": "tesseract_ocr", "sha256": digest, "synthetic": False
                        })
                except ImportError as exc:
                    raise RuntimeError('OCR needs optional dependencies: pip install -e ".[ocr]" and the Tesseract binary') from exc
            if not page_text and not (ocr_empty_pages and any(r.get("page") == page_no and r.get("extractor") == "tesseract_ocr" for r in records)):
                records.append({
                    "element_id": f"{canonical_doc_id}-P{page_no}-OCR-NEEDED",
                    "doc_id": canonical_doc_id, "revision": revision,
                    "section_number": section, "section": section, "page": page_no,
                    "element_type": "ocr_needed", "text": "",
                    "extractor": "pymupdf_empty_page", "needs_ocr": True,
                    "synthetic": False
                })
            if image_dir:
                pix = page.get_pixmap(matrix=fitz.Matrix(1.5, 1.5), alpha=False)
                pix.save(image_dir / f"{canonical_doc_id}-P{page_no}.png")
                # Preserve embedded page images as figure candidates with bounding boxes.
                for ibidx, block in enumerate(page.get_text("dict").get("blocks", [])):
                    if block.get("type") != 1 or not block.get("image"):
                        continue
                    ext = block.get("ext", "png")
                    image_name = f"{canonical_doc_id}-P{page_no}-IMG{ibidx+1}.{ext}"
                    image_path = image_dir / image_name
                    image_path.write_bytes(block["image"])
                    bbox = [round(float(v), 2) for v in block.get("bbox", [])]
                    records.append({
                        "element_id": f"{canonical_doc_id}-P{page_no}-IMG{ibidx+1}",
                        "doc_id": canonical_doc_id, "revision": revision,
                        "section_number": section, "section": section,
                        "section_title": section_title, "page": page_no, "bbox": bbox,
                        "element_type": "figure_candidate", "image_path": str(image_path),
                        "text": f"Embedded figure/image candidate on page {page_no}; caption must be verified manually.",
                        "extractor": "pymupdf_embedded_image", "sha256": digest, "synthetic": False
                    })
    write_jsonl(records, output)
    return records

def _table_markdown(rows: list[list[str]]) -> str:
    if not rows: return ""
    width = max(len(row) for row in rows)
    normalized = [row + [""] * (width - len(row)) for row in rows]
    header = normalized[0]
    sep = ["---"] * width
    lines = ["| " + " | ".join(header) + " |", "| " + " | ".join(sep) + " |"]
    lines.extend("| " + " | ".join(row) + " |" for row in normalized[1:])
    return "\n".join(lines)
