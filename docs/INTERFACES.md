# Shared interfaces and data contracts

## Element JSONL schema
Each line is a source element with at minimum:
- `element_id` (string, unique within a document/revision namespace)
- `doc_id`, `revision`, `section_number`/`section`, `section_title`
- `page` (1-based integer), `bbox` (optional `[x0,y0,x1,y1]` in PDF points)
- `element_type` (`paragraph`, `table`, `figure_candidate`, `ocr_text`, `ocr_needed`, `parser_warning`, ...)
- `text` (searchable content), `extractor`, `synthetic`
- Optional `markdown`, `table_json`, `image_path`, `sha256`, `needs_ocr`

Generic extraction marks revision and section as unknown unless confidently inferred. Do not invent these fields. Validate/fix them through a reviewed source-specific parser.

## Chunk contract
Current retrieval treats each element as one atomic unit. A future structure-aware chunker should preserve `parent_element_id`, section hierarchy, table/figure atomicity, and source provenance.

## Knowledge graph
- Node: `id`, `type`, optional aliases and provenance list.
- Edge: `source`, `relation`, `target`, `provenance`, `extraction_method`.
- Provenance includes document, revision, section, page, element ID, and bounding box where available.
- `build_graph(records)` returns `{nodes, edges, metadata}`. `graph_query(graph, entity, relation=None)` returns matching entities and adjacent edges.

## Retrieval API
- `lexical_search(query, records, k=10)` → ranked records with `lexical_score`.
- `dense_search(query, records, k=10, model_name=...)` → ranked records with `dense_score`; optional local sentence-transformers dependency.
- `reciprocal_rank_fusion(*rankings, k=10)` → fused records with `rrf_score`.
- `search(query, records, k=5, mode='hybrid')` → ranked records with `score` and `retrieval_mode`. Hybrid explicitly falls back to lexical mode when dense dependencies are unavailable.

## Agent / citation contract
`run_agent(question, records, k=6, max_steps=4, min_score=0.2, retrieval_mode='hybrid')` returns `answer`, `citations`, `declined`, `evidence`, `plan`, `trace`, `latency_ms`, `graph_context`, and `limits`. The citation verifier currently checks source-element membership, not semantic claim entailment; do not overstate it.

Citation format: `[doc_id, rev. revision, §section, p. page, element_id]`.

## Gold-set format
Each JSON row should include `id`, `question`, `category`, `author`, `gold_answer`, `gold_element_ids`, and `verifier`. The executable metric harness reads `id`, `question`, `gold_element_ids`, and `category`. A reviewer must verify the answer and element IDs against the actual PDF.

## Trace and logging
Each trace entry has `step`, `action`, and action-specific details. CLI logs go to stderr; structured result/trace JSON is written to stdout. The trace is deterministic except for measured latency and optional model behavior.
