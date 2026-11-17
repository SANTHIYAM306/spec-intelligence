"""Conservative multi-page table continuation detection.

Only stitches tables when document/revision match, pages are adjacent and normalized headers
match exactly. The original table elements are retained and the stitched element cites all
source element IDs. This heuristic must be manually validated on the real corpus.
"""
from __future__ import annotations
import re
from typing import Any

def _norm_cell(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())

def _header(table: dict[str, Any]) -> tuple[str, ...]:
    rows = table.get("table_json")
    if isinstance(rows, list) and rows:
        return tuple(_norm_cell(x) for x in rows[0])
    text = str(table.get("markdown", table.get("text", ""))).splitlines()
    for line in text:
        if line.strip().startswith("|") and "---" not in line:
            return tuple(_norm_cell(x) for x in line.strip().strip("|").split("|"))
    return ()

def stitch_table_continuations(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    tables = [r for r in records if str(r.get("element_type", "")).lower() == "table"]
    tables.sort(key=lambda r: (str(r.get("doc_id")), str(r.get("revision")), int(r.get("page") or 0),
                              str(r.get("element_id"))))
    groups: list[list[dict[str, Any]]] = []
    for table in tables:
        header = _header(table)
        if not header:
            continue
        if groups:
            prev = groups[-1][-1]
            same_doc = (table.get("doc_id"), table.get("revision")) == (prev.get("doc_id"), prev.get("revision"))
            adjacent = int(table.get("page") or 0) == int(prev.get("page") or 0) + 1
            same_header = header == _header(groups[-1][0])
            if same_doc and adjacent and same_header:
                groups[-1].append(table); continue
        groups.append([table])
    stitched = []
    for group in groups:
        if len(group) < 2:
            continue
        rows: list[list[str]] = []
        for idx, item in enumerate(group):
            raw = item.get("table_json")
            if not isinstance(raw, list):
                raw = [[cell.strip() for cell in line.strip().strip("|").split("|")]
                       for line in str(item.get("markdown", item.get("text", ""))).splitlines()
                       if line.strip().startswith("|") and "---" not in line]
            if idx and raw and tuple(_norm_cell(x) for x in raw[0]) == _header(group[0]):
                raw = raw[1:]
            rows.extend([[str(cell or "").strip() for cell in row] for row in raw])
        first, last = group[0], group[-1]
        md = ""
        if rows:
            width = max(len(row) for row in rows)
            rows = [row + [""]*(width-len(row)) for row in rows]
            md = "| " + " | ".join(rows[0]) + " |\n| " + " | ".join(["---"]*width) + " |\n"
            md += "\n".join("| " + " | ".join(row) + " |" for row in rows[1:])
        stitched.append({**first, "element_id": f"{first.get('element_id')}--stitched--{last.get('element_id')}",
          "element_type": "stitched_table", "page": first.get("page"), "page_start": first.get("page"),
          "page_end": last.get("page"), "source_element_ids": [x.get("element_id") for x in group],
          "table_json": rows, "markdown": md, "text": md,
          "extractor": "header_match_stitching_heuristic", "stitch_confidence": 0.65,
          "stitch_warning": "Candidate stitching: inspect original pages and verify repeated headers/caption."})
    return stitched
