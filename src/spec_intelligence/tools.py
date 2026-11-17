"""Typed local tools exposed to the agent."""
from __future__ import annotations
from typing import Any
from .graph import build_graph, graph_query, graph_path, resolve_entity
from .retrieval import search
from .vision import search_pages as _search_pages

def search_text(query: str, records: list[dict[str, Any]], k: int = 5,
                filters: dict[str, Any] | None = None, mode: str = "hybrid",
                rerank: bool = False) -> list[dict[str, Any]]:
    return search(query, records, k=k, mode=mode, filters=filters, rerank=rerank)

def search_pages(query: str, page_index: list[dict[str, Any]], k: int = 5,
                 model_name: str = "vidore/colqwen2.5-v0.2") -> list[dict[str, Any]]:
    return _search_pages(query, page_index, k=k, model_name=model_name)

def get_section(records: list[dict[str, Any]], doc_id: str, section_number: str) -> list[dict[str, Any]]:
    found = [r for r in records if r.get("doc_id") == doc_id and
             str(r.get("section_number", r.get("section", ""))) == str(section_number)]
    return sorted(found, key=lambda r: (int(r.get("page") or 0), str(r.get("element_id", ""))))

def get_table(records: list[dict[str, Any]], table_id: str) -> dict[str, Any] | None:
    for r in records:
        if r.get("element_id") == table_id and str(r.get("element_type", "")).lower() in {"table", "stitched_table"}:
            return {"element": r, "markdown": r.get("markdown", r.get("text", "")),
                    "table_json": r.get("table_json"), "citation": {k: r.get(k) for k in
                    ("doc_id", "revision", "section_number", "page", "bbox", "element_id")}}
    return None

def get_figure(records: list[dict[str, Any]], figure_id: str) -> dict[str, Any] | None:
    for r in records:
        if r.get("element_id") == figure_id and str(r.get("element_type", "")).lower() in {
            "figure", "diagram", "image", "structured_figure"}:
            return {"element": r, "image_path": r.get("image_path"), "figure_json": r.get("figure_json"),
                    "citation": {k: r.get(k) for k in
                    ("doc_id", "revision", "section_number", "page", "bbox", "element_id")}}
    return None

def graph_tool(records: list[dict[str, Any]], entity: str, relation: str | None = None) -> dict[str, Any]:
    return graph_query(build_graph(records), entity, relation)

def resolve_entity_tool(records: list[dict[str, Any]], name: str) -> list[dict[str, Any]]:
    return resolve_entity(name, build_graph(records))

def graph_path_tool(records: list[dict[str, Any]], source: str, target: str,
                    max_depth: int = 5) -> dict[str, Any]:
    return graph_path(build_graph(records), source, target, max_depth)

def tool_schemas() -> list[dict[str, Any]]:
    return [
      {"name":"search_text","input":{"query":"string","k":"integer","filters":"object"},"output":"ranked evidence elements"},
      {"name":"search_pages","input":{"query":"string","k":"integer"},"output":"ranked page images with vision scores"},
      {"name":"graph_query","input":{"entity":"string","relation":"optional string"},"output":"nodes and provenance-rich edges"},
      {"name":"get_section","input":{"doc_id":"string","section_number":"string"},"output":"ordered elements"},
      {"name":"get_table","input":{"table_id":"string"},"output":"Markdown, JSON and citation"},
      {"name":"get_figure","input":{"figure_id":"string"},"output":"image path, structured JSON and citation"},
      {"name":"resolve_entity","input":{"name":"string"},"output":"candidate canonical graph entities"},
      {"name":"graph_path","input":{"source":"string","target":"string","max_depth":"integer"},"output":"shortest provenance-bearing path"}]
