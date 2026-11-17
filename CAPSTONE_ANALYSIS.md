# Reference capstone analysis and gap review

## Reference design described by the assignment
The assignment's reference capstone is vision-first: render PDF pages to images, index page images using ColQwen2.5/ColPali late-interaction multi-vectors, retrieve by MaxSim, and answer from top page images with page citations and evidence regions. It compares that path against OCR-then-text retrieval across prose, dense tables, charts and equations.

## What transfers
- Page-image rendering and page-level provenance.
- Late-interaction retrieval as an alternative for diagrams and complex layout.
- Text-vs-vision comparison and content-type stratification.
- Evidence-region citations and reproducible evaluation.

## What changes for the specification corpus
- Add typed text/table/figure elements and section-aware parent-child chunking.
- Namespace IDs by document and revision because table/figure numbering restarts.
- Preserve exact test IDs and timer/state/message identifiers using lexical search.
- Stitch multi-page tables with repeated headers.
- Link compliance test cases to base-spec requirements, states, timers and messages.
- Detect stale cross-references caused by specification revision changes.
- Add graph and agent tools, a bounded execution trace, citation verification and explicit declines.

## Current implementation boundary
The repository provides PDF text/table ingestion, optional OCR, page rendering, optional ColQwen adapter, lexical/dense/hybrid retrieval, candidate graph extraction and a bounded deterministic evidence workflow. The model-backed vision and OCR benchmark have not been run here. No performance claim is made until the authorised source pages and model hardware are available.
