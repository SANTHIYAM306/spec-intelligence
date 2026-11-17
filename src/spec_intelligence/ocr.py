"""Optional Tesseract OCR for scanned pages; emits typed page-level provenance."""
from __future__ import annotations
from pathlib import Path
from typing import Any

def ocr_image(image_path: str | Path, doc_id: str, page: int, revision: str = "unknown",
              language: str = "eng") -> list[dict[str, Any]]:
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise RuntimeError('Install OCR extras: pip install -e ".[ocr]" and install Tesseract binary') from exc
    image = Image.open(image_path).convert("RGB")
    data = pytesseract.image_to_data(image, lang=language, output_type=pytesseract.Output.DICT)
    words_by_line: dict[tuple[int, int, int], list[int]] = {}
    for i, word in enumerate(data["text"]):
        if str(word).strip() and int(data["conf"][i]) >= 0:
            key = (int(data["block_num"][i]), int(data["par_num"][i]), int(data["line_num"][i]))
            words_by_line.setdefault(key, []).append(i)
    result = []
    for line_idx, indices in enumerate(words_by_line.values(), 1):
        text = " ".join(data["text"][i].strip() for i in indices).strip()
        if not text: continue
        x0 = min(int(data["left"][i]) for i in indices); y0 = min(int(data["top"][i]) for i in indices)
        x1 = max(int(data["left"][i])+int(data["width"][i]) for i in indices)
        y1 = max(int(data["top"][i])+int(data["height"][i]) for i in indices)
        result.append({"element_id": f"{doc_id}-P{page}-OCR-L{line_idx}", "doc_id": doc_id,
          "revision": revision, "page": page, "section_number": "unknown", "section": "unknown",
          "section_title": "unknown", "bbox": [x0,y0,x1,y1], "element_type": "ocr_line",
          "text": text, "extractor": "tesseract", "image_path": str(image_path),
          "ocr_confidence": round(sum(float(data["conf"][i]) for i in indices)/len(indices), 2),
          "synthetic": False})
    return result
