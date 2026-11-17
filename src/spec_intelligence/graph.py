"""Provenance-rich lightweight knowledge graph and graph query helpers."""
from __future__ import annotations
import re
from typing import Any

ENTITY_PATTERNS = [
    ("Check", re.compile(r"\[(?:TEST(?:\.[A-Z0-9_-]+)+|TD\.?[A-Z0-9.]+)#[A-Z0-9.]+\]")),
    ("TestCase", re.compile(r"\b(?:TEST(?:\.[A-Z0-9_-]+)+|TD\s*\d+(?:\.\d+)+|[A-Z]{2,5}\.[A-Z0-9.]+)\b")),
    ("Timer", re.compile(r"\bt[A-Z][A-Za-z0-9_]*\b")),
    ("Counter", re.compile(r"\bn[A-Z][A-Za-z0-9_]*\b")),
    ("State", re.compile(r"\b(?:PE_[A-Z0-9_]+|PRL_[A-Z0-9_]+|Try\.(?:SRC|SNK)|Unattached\.(?:SRC|SNK)|AttachWait\.(?:SRC|SNK))\b")),
    ("Message", re.compile(r"\b(?:Source_Capabilities|Request|Accept|PS_RDY|GoodCRC|Enter_USB|Get_Source_Cap|Soft_Reset|Hard_Reset)\b")),
    ("DataObject", re.compile(r"\b(?:PDO|APDO|RDO|VDO|SPR PPS|EPR AVS)\b")),
    ("Requirement", re.compile(r"\b(?:R-[A-Z0-9-]+|[A-Z]{2,8}_[A-Z0-9_]*SHALL[A-Z0-9_]*)\b")),
    ("VIFField", re.compile(r"\b(?:PD_Port_Type|Type_C_State_Machine|[A-Za-z0-9_]*VIF[A-Za-z0-9_]*)\b")),
    ("Signal", re.compile(r"\b(?:CC1|CC2|VBUS|VCONN|Rp|Rd|Ra)\b")),
    ("PowerProfile", re.compile(r"\b(?:BPP|EPP|MPP)\b")),
]
RELATION_PATTERNS = [
    (re.compile(r"([A-Z][A-Z0-9_.-]+)\s+(?:verifies|tests|checks)\s+(?:requirement\s+)?([A-Z][A-Z0-9_.-]+)", re.I), "VERIFIES"),
    (re.compile(r"([A-Za-z][A-Za-z0-9_.-]+)\s+(?:is defined in|defined in|see)\s+(?:Section\s+|§)?(\d+(?:[.-]\d+)+)", re.I), "DEFINED_IN"),
    (re.compile(r"\b(Source_Capabilities|Request|Accept|PS_RDY|GoodCRC|Enter_USB)\b.{0,120}\b(t[A-Z][A-Za-z0-9_]+)\b"), "USES_TIMER"),
]

def build_graph(records: list[dict[str, Any]]) -> dict[str, Any]:
    nodes: dict[str, dict[str, Any]] = {}
    edges: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for rec in records:
        text = str(rec.get("text", ""))
        provenance = {k: rec.get(k) for k in ("doc_id", "revision", "section", "section_number", "page", "element_id", "bbox")}
        found: list[tuple[str, str, int, int]] = []
        for typ, pattern in ENTITY_PATTERNS:
            for match in pattern.finditer(text):
                name = match.group(0).strip()
                canonical = re.sub(r"\s+", " ", name)
                nodes.setdefault(canonical.lower(), {"id": canonical, "type": typ, "aliases": [], "provenance": []})
                nodes[canonical.lower()]["provenance"].append(provenance)
                found.append((canonical, typ, match.start(), match.end()))
        # Anchor entity mentions to the document section and table/figure elements.
        section = rec.get("section_number", rec.get("section"))
        if section and section != "unknown":
            sec_id = f"{rec.get('doc_id','doc')}::section::{section}"
            nodes.setdefault(sec_id.lower(), {"id": sec_id, "type": "Section", "provenance": [provenance]})
            for name, _, _, _ in found:
                key = (name.lower(), "DEFINED_IN", sec_id.lower(), str(rec.get("element_id", "")))
                edges.setdefault(key, {"source": name, "relation": "DEFINED_IN", "target": sec_id,
                    "provenance": provenance, "extraction_method": "rule", "confidence": 0.55})
        for pattern, relation in RELATION_PATTERNS:
            for match in pattern.finditer(text):
                source, target = match.group(1), match.group(2)
                for name, typ in ((source, "Entity"), (target, "Entity")):
                    nodes.setdefault(name.lower(), {"id": name, "type": typ, "aliases": [], "provenance": [provenance]})
                key = (source.lower(), relation, target.lower(), str(rec.get("element_id", "")))
                edges.setdefault(key, {"source": source, "relation": relation, "target": target,
                    "provenance": provenance, "extraction_method": "rule", "confidence": 0.65})
    return {"nodes": list(nodes.values()), "edges": list(edges.values()), "metadata": {
        "method": "regex and mention anchoring", "record_count": len(records),
        "warning": "Candidate graph only: validate extracted triples against source evidence."
    }}

def resolve_entity(name: str, graph: dict[str, Any]) -> list[dict[str, Any]]:
    q = re.sub(r"\s+", " ", name.strip()).lower()
    exact = [n for n in graph.get("nodes", []) if n.get("id", "").lower() == q]
    if exact: return exact
    return [n for n in graph.get("nodes", []) if q in n.get("id", "").lower() or n.get("id", "").lower() in q]

def graph_query(graph: dict[str, Any], entity: str, relation: str | None = None) -> dict[str, Any]:
    nodes = resolve_entity(entity, graph)
    ids = {n["id"].lower() for n in nodes}
    edges = [e for e in graph.get("edges", []) if
             (e.get("source", "").lower() in ids or e.get("target", "").lower() in ids)
             and (relation is None or e.get("relation") == relation)]
    return {"entities": nodes, "edges": edges}


ONTOLOGY_RELATIONS = {
    "DEFINED_IN", "REFERENCES", "SENT_BY", "RESPONDS_TO", "CONTAINS",
    "TRANSITIONS_TO", "STARTS_TIMER", "STOPS_TIMER", "HAS_FIELD", "HAS_VALUE",
    "TESTS", "VERIFIES", "APPLIES_WHEN", "TUNNELS", "SUPERSEDES", "USES_TIMER"
}

def validate_graph(graph: dict[str, Any]) -> dict[str, Any]:
    """Validate relation names, endpoints and mandatory provenance without deleting candidates."""
    node_ids = {str(n.get("id", "")).lower() for n in graph.get("nodes", [])}
    invalid = []
    for edge in graph.get("edges", []):
        reasons = []
        if edge.get("relation") not in ONTOLOGY_RELATIONS: reasons.append("unknown_relation")
        if str(edge.get("source", "")).lower() not in node_ids: reasons.append("missing_source_node")
        if str(edge.get("target", "")).lower() not in node_ids: reasons.append("missing_target_node")
        prov = edge.get("provenance") or {}
        if not all(prov.get(k) is not None for k in ("doc_id", "page", "element_id")):
            reasons.append("missing_provenance")
        if reasons: invalid.append({"edge": edge, "reasons": reasons})
    return {"valid_edge_count": len(graph.get("edges", []))-len(invalid),
            "invalid_edge_count": len(invalid), "invalid_edges": invalid}

def graph_statistics(graph: dict[str, Any]) -> dict[str, Any]:
    from collections import Counter
    node_counts = Counter(n.get("type", "Unknown") for n in graph.get("nodes", []))
    edge_counts = Counter(e.get("relation", "Unknown") for e in graph.get("edges", []))
    connected = set()
    for e in graph.get("edges", []):
        connected.add(str(e.get("source", "")).lower()); connected.add(str(e.get("target", "")).lower())
    orphans = [n.get("id") for n in graph.get("nodes", []) if str(n.get("id", "")).lower() not in connected]
    return {"node_count": len(graph.get("nodes", [])), "edge_count": len(graph.get("edges", [])),
            "nodes_by_type": dict(node_counts), "edges_by_relation": dict(edge_counts),
            "orphan_count": len(orphans), "orphan_nodes": orphans,
            "validation": validate_graph(graph)}


def graph_path(graph: dict[str, Any], source: str, target: str, max_depth: int = 5) -> dict[str, Any]:
    """Breadth-first path search over known graph edges, preserving the selected edge provenance."""
    from collections import deque
    if max_depth < 1: raise ValueError("max_depth must be >= 1")
    src_nodes, dst_nodes = resolve_entity(source, graph), resolve_entity(target, graph)
    src_ids = {n["id"].lower() for n in src_nodes}; dst_ids = {n["id"].lower() for n in dst_nodes}
    if not src_ids or not dst_ids:
        return {"found": False, "path": [], "reason": "source_or_target_entity_not_found"}
    if src_ids & dst_ids:
        return {"found": True, "path": [{"node": next(n for n in graph["nodes"] if n["id"].lower() in src_ids)}], "edges": []}
    adjacency: dict[str, list[tuple[str, dict[str, Any]]]] = {}
    for edge in graph.get("edges", []):
        a, b = str(edge.get("source", "")).lower(), str(edge.get("target", "")).lower()
        adjacency.setdefault(a, []).append((b, edge))
        adjacency.setdefault(b, []).append((a, edge))
    queue = deque((node, [node], []) for node in src_ids)
    visited = set(src_ids)
    while queue:
        node, nodes_path, edges_path = queue.popleft()
        if len(edges_path) >= max_depth: continue
        for neighbor, edge in adjacency.get(node, []):
            if neighbor in visited: continue
            next_nodes, next_edges = nodes_path + [neighbor], edges_path + [edge]
            if neighbor in dst_ids:
                node_lookup = {n["id"].lower(): n for n in graph.get("nodes", [])}
                return {"found": True, "path": [node_lookup.get(n, {"id": n}) for n in next_nodes],
                        "edges": next_edges}
            visited.add(neighbor); queue.append((neighbor, next_nodes, next_edges))
    return {"found": False, "path": [], "reason": "no_path_within_depth", "max_depth": max_depth}
