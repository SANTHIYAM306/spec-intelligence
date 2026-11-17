"""Page-image rendering and optional vision retrieval interfaces.

This module deliberately separates page rendering from model inference. A rendered page
is not a vision embedding, and the fallback pixel descriptor is not represented as a
ColPali/ColQwen model.
"""
from __future__ import annotations
import hashlib, json
from pathlib import Path
from typing import Any

def render_pdf_pages(pdf_path: str | Path, output_dir: str | Path, dpi: int = 165,
                     page_numbers: list[int] | None = None) -> list[dict[str, Any]]:
    try: import fitz
    except ImportError as exc: raise RuntimeError('Install PDF support: pip install -e ".[pdf]"') from exc
    source, dest = Path(pdf_path), Path(output_dir)
    if dpi < 72 or dpi > 300: raise ValueError("dpi must be between 72 and 300")
    dest.mkdir(parents=True, exist_ok=True)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    manifest = []
    with fitz.open(source) as doc:
        selected = page_numbers or list(range(1, len(doc)+1))
        for n in selected:
            if n < 1 or n > len(doc): raise ValueError(f"Page {n} outside 1..{len(doc)}")
            page = doc[n-1]
            pix = page.get_pixmap(matrix=fitz.Matrix(dpi/72, dpi/72), alpha=False)
            path = dest / f"{source.stem}-p{n:04d}.png"
            pix.save(path)
            manifest.append({"doc_id": source.stem, "page": n, "image_path": str(path),
                             "dpi": dpi, "sha256": digest, "width": pix.width, "height": pix.height})
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest

def maxsim_score(query_vectors, page_vectors) -> float:
    """ColBERT-style MaxSim primitive: sum over query vectors of max page-token similarity."""
    import numpy as np
    q, p = np.asarray(query_vectors), np.asarray(page_vectors)
    if q.ndim != 2 or p.ndim != 2 or q.shape[1] != p.shape[1]:
        raise ValueError("Expected 2D query/page vector matrices with matching embedding dimensions")
    if not len(q) or not len(p): return 0.0
    q = q / np.maximum(np.linalg.norm(q, axis=1, keepdims=True), 1e-12)
    p = p / np.maximum(np.linalg.norm(p, axis=1, keepdims=True), 1e-12)
    return float((q @ p.T).max(axis=1).sum())

def search_pages(query: str, page_index: list[dict[str, Any]], k: int = 5,
                 model_name: str = "vidore/colqwen2.5-v0.2") -> list[dict[str, Any]]:
    """Optional ColQwen page search adapter; requires Transformers, torch and model weights.

    The implementation is intentionally explicit about runtime requirements. It refuses
    to silently substitute text search for visual retrieval.
    """
    try:
        import torch
        from colpali_engine.models import ColQwen2_5, ColQwen2_5Processor
    except ImportError as exc:
        raise RuntimeError('Vision retrieval requires PyTorch and colpali-engine: pip install -e ".[vision]"') from exc
    if not page_index: return []
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = ColQwen2_5.from_pretrained(model_name).eval().to(device)
    processor = ColQwen2_5Processor.from_pretrained(model_name)
    query_inputs = processor.process_queries([query]).to(device)
    with torch.no_grad():
        qemb = model(**query_inputs)
    scores = []
    for item in page_index:
        path = item.get("image_path")
        if not path or not Path(path).is_file(): continue
        from PIL import Image
        image = Image.open(path).convert("RGB")
        inputs = processor.process_images([image]).to(device)
        with torch.no_grad(): pemb = model(**inputs)
        score = processor.score_multi_vector(qemb, pemb).flatten()[0].item()
        scores.append(({**item, "vision_score": float(score), "retrieval_mode": "colqwen2.5"}, float(score)))
    scores.sort(key=lambda x: x[1], reverse=True)
    return [x[0] for x in scores[:k]]
