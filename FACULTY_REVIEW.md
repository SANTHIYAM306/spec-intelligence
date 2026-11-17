# Faculty review checklist — implementation and evidence status

This checklist is deliberately conservative: implemented code, locally verified behavior, and unrun model/corpus work are separate.

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Local CLI and clean package structure | Implemented | `specqa demo`, `ask`, `ingest`, `chunk`, `stitch-tables`, `render`, `ocr`, `graph`, `eval`, `ablate` |
| Unit tests | Verified locally | 25 tests pass in this environment; run `pytest` after clean install |
| PDF text extraction | Implemented baseline | PyMuPDF blocks, page, bbox, source SHA-256, optional revision/doc ID |
| Table extraction | Partial | Best-effort PyMuPDF table-to-Markdown/JSON; heuristic adjacent-page stitching candidate; manually validate every stitched table |
| OCR | Partial | Tesseract line extraction; Unlimited-OCR required by assignment is not integrated/run |
| Figure/diagram structuring | Partial | Embedded-image extraction, page rendering and figure JSON schema validation; no VLM extraction run or 10-figure accuracy audit |
| Dense retrieval | Implemented optional | sentence-transformers cosine retrieval and process-local cache; model download/inference not verified against real specs |
| Hybrid retrieval / reranker | Implemented optional | BM25-style lexical + dense RRF; optional cross-encoder; falls back transparently when dense dependency unavailable |
| Vision-native retrieval | Adapter/primitive present, unverified | ColQwen2.5 adapter, page rendering and MaxSim primitive; no full index build or real page retrieval benchmark |
| Knowledge graph | Baseline implemented | Identifier patterns, section anchoring, graph stats/validation/path helper; no LLM/VLM extraction or audited triple precision |
| Agentic RAG | Partial | Plan, text retrieval, graph lookup, one corrective lexical retry, citation-ID validation and trace; optional local LLM JSON generation not tested with actual model weights |
| Citation verification | Partial | Validates cited element IDs belong to retrieved evidence; does not prove claim entailment/region correctness semantically |
| Real seven-source corpus | Not available in this ZIP | Add locally authorised source files and complete actual SHA-256/page inventory; never commit licensed source content |
| Verified 60-question gold set | Template only | 25 Appendix A seed questions included without invented answers; author and verify evidence against actual PDFs, then expand to 60 |
| OCR benchmark / content matrix / A–F ablations | Not measured | Scripts/templates included; real labelled pages, models and same verified gold set required |
| Full assignment target | Not demonstrated yet | Requires actual corpus, hardware/model runs, manual audits, 60 verified questions and held-out evaluation |

## Suggested demonstration
1. `specqa demo` shows only synthetic fixture behavior.
2. Ingest one locally authorised PDF with its exact revision and inspect the JSONL provenance.
3. Run `specqa chunk` and `specqa stitch-tables`; inspect candidates against original pages.
4. Run lexical search first. Enable dense/rerank only after optional dependencies and model weights are available.
5. Render a few pages and run ColQwen only where hardware supports it.
6. Ask a known out-of-corpus question and demonstrate a decline.
7. Explain that source-level accuracy, OCR/vision results, KG precision and A–F scores are pending rather than inventing them.

No grade can be guaranteed from this checklist. The remaining source-dependent work is material to the assignment rubric.
