# WS3 exploration — knowledge graph

## Question
How can test cases link to requirements, timers, states and messages across documents without losing evidence provenance?

## Candidate approaches
- Deterministic extraction for strict identifiers and section references.
- Schema-constrained LLM/VLM extraction for relations expressed in prose, tables and figures.
- NetworkX/JSON for portable local storage versus a graph database if corpus scale demands it.

## Current implementation
`graph.py` extracts candidate identifiers with patterns, anchors entities to sections, exposes entity resolution and graph query helpers, and reports graph statistics/validation. Every candidate edge retains source metadata and extraction confidence.

## Risks and next steps
Pattern matching misses paraphrases and can create false positives. Add schema domain/range constraints, span-level evidence, entity merge logs, cross-document resolution and stale revision checks. Audit a random 100-triple sample manually before reporting precision. No triple precision is currently measured.
