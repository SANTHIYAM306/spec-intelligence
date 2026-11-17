"""Structure-aware chunking with stable parent-child links and source provenance."""
from __future__ import annotations
import re
from typing import Any

def chunk_elements(records: list[dict[str, Any]], max_chars: int = 1400, overlap: int = 120) -> list[dict[str, Any]]:
    """Keep tables/figures atomic; split prose on paragraph boundaries and retain parent metadata."""
    if max_chars < 100 or overlap < 0 or overlap >= max_chars:
        raise ValueError("Require max_chars >= 100 and 0 <= overlap < max_chars")
    out: list[dict[str, Any]] = []
    for rec in records:
        text = str(rec.get("text", "")).strip()
        if not text:
            continue
        typ = str(rec.get("element_type", "paragraph")).lower()
        if typ in {"table", "stitched_table", "figure", "diagram", "image", "structured_figure"} or len(text) <= max_chars:
            pieces = [text]
        else:
            paragraphs = [p.strip() for p in re.split(r"\n\s*\n", text) if p.strip()]
            pieces, current = [], ""
            for para in paragraphs or [text]:
                if len(para) > max_chars:
                    if current: pieces.append(current); current = ""
                    start = 0
                    while start < len(para):
                        end = min(len(para), start + max_chars)
                        pieces.append(para[start:end])
                        if end == len(para): break
                        start = end - overlap
                elif not current:
                    current = para
                elif len(current) + len(para) + 2 <= max_chars:
                    current += "\n\n" + para
                else:
                    pieces.append(current); current = para
            if current: pieces.append(current)
        parent_id = str(rec.get("element_id", f"element-{len(out)}"))
        for idx, piece in enumerate(pieces, 1):
            child = dict(rec)
            child.update({"element_id": f"{parent_id}::chunk-{idx}", "parent_id": parent_id,
                          "chunk_index": idx, "chunk_count": len(pieces), "text": piece,
                          "chunking_method": "atomic" if len(pieces) == 1 else "section-aware"})
            out.append(child)
    return out
