"""Synthetic fixture corpus and JSONL loading utilities."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEMO_RECORDS: list[dict[str, Any]] = [
    {
        "element_id": "SYN-001",
        "doc_id": "SYNTHETIC-PD-SPEC",
        "revision": "SYN-0.1",
        "section": "4.1",
        "page": 3,
        "element_type": "paragraph",
        "text": "Synthetic example requirement R-100 states that a receiver must acknowledge the request before the example timer expires.",
        "synthetic": True,
    },
    {
        "element_id": "SYN-002",
        "doc_id": "SYNTHETIC-PD-TEST",
        "revision": "SYN-0.1",
        "section": "2.3",
        "page": 8,
        "element_type": "paragraph",
        "text": "Synthetic test TEST-100 verifies requirement R-100 by checking that the receiver acknowledgement occurs before the example timer expires.",
        "synthetic": True,
    },
    {
        "element_id": "SYN-003",
        "doc_id": "SYNTHETIC-PD-SPEC",
        "revision": "SYN-0.1",
        "section": "4.2",
        "page": 4,
        "element_type": "table",
        "text": "Synthetic table: Parameter EXAMPLE_TIMER. Illustrative value only: 100 ms. This is invented demo data, not a USB specification value.",
        "synthetic": True,
    },
    {
        "element_id": "SYN-004",
        "doc_id": "SYNTHETIC-TYPEC-SPEC",
        "revision": "SYN-0.1",
        "section": "1.2",
        "page": 2,
        "element_type": "paragraph",
        "text": "Synthetic note: connector state EXAMPLE_ATTACHED is an illustrative state used only for testing the demo pipeline.",
        "synthetic": True,
    },
]


def load_jsonl(path: str | Path) -> list[dict[str, Any]]:
    """Load JSON objects, one per line."""
    records: list[dict[str, Any]] = []
    with Path(path).open("r", encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if line.strip():
                try:
                    item = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ValueError(f"Invalid JSON on line {line_number}: {exc}") from exc
                if not isinstance(item, dict) or "text" not in item:
                    raise ValueError(f"Line {line_number} must be an object containing 'text'")
                records.append(item)
    return records


def write_jsonl(records: list[dict[str, Any]], path: str | Path) -> None:
    """Write JSON objects as UTF-8 JSONL."""
    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    with destination.open("w", encoding="utf-8") as stream:
        for record in records:
            stream.write(json.dumps(record, ensure_ascii=False) + "\n")
