# Completion roadmap ordered by evidence dependency

## Gate 1 — real corpus and ingestion
- Obtain the seven authorised source groups listed in the assignment; store them locally, never commit them.
- Complete `CORPUS.md` with actual revisions, dates, SHA-256, page counts and difficult pages.
- Compare PyMuPDF and pdfplumber on the same 20 pages; add manual text/table/reading-order labels and fidelity scores.
- Validate section hierarchy against each source; improve caption attachment, source-specific section parsing and multi-page table stitching.
- Hand-check stitched table candidates before treating them as correct.

## Gate 2 — OCR and vision
- Hand-label the assignment's ~40-page OCR benchmark, with at least 15 fully labelled pages.
- Run Unlimited-OCR in single-page and multi-page modes on local authorised pages; record GPU/RAM, model version, time, text accuracy, table fidelity and failure cases.
- Build the ColQwen2.5/MaxSim page index on gold pages plus a random sample if GPU is constrained.
- Produce structured state-machine/timing JSON from figure crops and manually verify 10 examples.
- Measure text-only, vision-only and fused retrieval by content type.

## Gate 3 — retrieval and graph
- Build a persistent dense/vector index for large corpora; current dense vectors are cached in-process, not persisted.
- Expand ontology extraction to LLM/VLM relations with span provenance, schema domain/range checks, entity merge logs and stale revision detection.
- Audit a random 100-triple sample and calculate duplicate-entity rate.
- Add reliable cross-document linking between base specs and test specs; use source-verified test cases.

## Gate 4 — agent and evaluation
- Validate the optional local LLM generation with a supported locally stored model and manually audit claim entailment.
- Add per-tool timeouts, token accounting and stronger semantic/region-level citation verification.
- Build 60 independently verified gold questions and reserve the reviewer-held-out set.
- Run the content-type × approach matrix and valid A–F ablations on exactly the same gold set.
- Report answer correctness, faithfulness, citation accuracy, refusal accuracy, parsing quality, KG precision, p50/p95 latency and resource use.
- Show three real failures with traces and the changes made.

This repository includes code scaffolds and a runnable baseline, but the source-dependent evaluation gates are not complete. Complete them with recorded evidence before claiming assignment-level success.
