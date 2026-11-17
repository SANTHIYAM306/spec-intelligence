"""Schema validation for VLM-generated figure descriptions; does not call a hosted model."""
from __future__ import annotations
from typing import Any

def validate_figure_json(payload: dict[str, Any]) -> tuple[bool, list[str]]:
    errors = []
    kind = payload.get("figure_type")
    if kind not in {"state_machine", "timing_diagram", "flowchart", "block_diagram", "other"}:
        errors.append("figure_type must be one of state_machine, timing_diagram, flowchart, block_diagram, other")
    if not isinstance(payload.get("description"), str) or not payload.get("description", "").strip():
        errors.append("description must be a non-empty string")
    if not isinstance(payload.get("entities", []), list): errors.append("entities must be a list")
    if kind == "state_machine":
        if not isinstance(payload.get("states"), list): errors.append("states must be a list")
        if not isinstance(payload.get("transitions"), list): errors.append("transitions must be a list")
        for i, edge in enumerate(payload.get("transitions", [])):
            if not isinstance(edge, dict) or not all(k in edge for k in ("from", "to", "trigger")):
                errors.append(f"transitions[{i}] requires from, to, trigger")
    if kind == "timing_diagram":
        if not isinstance(payload.get("signals"), list): errors.append("signals must be a list")
        if not isinstance(payload.get("events"), list): errors.append("events must be a list")
        if not isinstance(payload.get("timers", []), list): errors.append("timers must be a list")
    return not errors, errors

def make_figure_element(doc_id: str, revision: str, page: int, element_id: str,
                        caption: str, image_path: str, payload: dict[str, Any],
                        section_number: str = "unknown", bbox: list[float] | None = None,
                        confidence: float | None = None) -> dict[str, Any]:
    valid, errors = validate_figure_json(payload)
    text = f"{caption}\n{payload.get('description','')}".strip()
    return {"element_id": element_id, "doc_id": doc_id, "revision": revision,
      "page": page, "section_number": section_number, "section": section_number,
      "element_type": "structured_figure", "caption": caption, "image_path": image_path,
      "bbox": bbox, "figure_json": payload, "figure_schema_valid": valid,
      "figure_validation_errors": errors, "confidence": confidence, "text": text,
      "extractor": "vlm_structured_output_pending_review", "synthetic": False}
