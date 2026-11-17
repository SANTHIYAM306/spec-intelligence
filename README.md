# Spec Intelligence

Local, evidence-grounded QA for technical specifications such as USB Power Delivery, USB Type-C, USB4 and Tech 2. This repository is a substantially improved **engineering prototype**. It is not a claim that the full assignment corpus or GPU-based visual path has been completed.

## Implemented in this repository

- Page/block-level PDF text extraction with source hash, page, section hint and bounding-box provenance.
- Recursive batch ingestion of locally licensed PDFs with a manifest for stable document/revision IDs, per-file failure reports, AppleDouble/`__MACOSX` filtering, exact-content duplicate reporting, and ID-collision checks.
- Optional table extraction as Markdown and JSON when the installed PyMuPDF version supports it.
- Optional page-image rendering for later OCR/vision processing. Empty-text pages are marked `ocr_needed`, not silently discarded.
- BM25-style lexical retrieval, optional local sentence-transformer dense retrieval, and Reciprocal Rank Fusion (RRF) hybrid retrieval. Dense retrieval is only active when its optional package/model is available; hybrid mode reports lexical fallback instead of pretending dense retrieval ran.
- Provenance-bearing graph candidates from identifier patterns, relation patterns and entity-to-section anchors, with entity resolution and graph query helpers.
- Bounded plan/retrieve/graph/reflect/verify workflow with a trace, latency, corrective lexical retry when first-pass retrieval is empty, and conservative evidence-only answer behavior. Optional local Transformers generation validates every claim's cited element IDs.
- Gold-set evaluation utility reporting Recall@k, MRR and category slices.
- Optional Tesseract OCR line extraction; OCR benchmark metric scaffold and two-parser speed/coverage comparison script.
- Optional ColQwen2.5 page-retrieval adapter and MaxSim primitive; optional local Transformers LLM answer generation with JSON schema and citation-ID validation.
- Parent-child structure-aware chunking, metadata filters, optional cross-encoder reranking, tool interfaces, graph stats/validation, tests and CI.

## Important gaps against the assignment

The assignment asks for the seven authorised source groups (~5,000 pages), an OCR benchmark that includes Unlimited-OCR, structured figure/state-machine/timing extraction, vision-native page retrieval (e.g. ColQwen2.5/MaxSim), a verified 60-question gold set and ablations A–F. Those cannot honestly be marked complete here: the source PDFs and labelled pages are not bundled, no Unlimited-OCR or GPU vision run has been measured, and no real-corpus gold answers have been verified. The graph extractor is a candidate-generation baseline, not an LLM-verified ontology pipeline. The answer layer returns cited evidence excerpts, not a general-purpose LLM synthesis.

No synthetic demo score should be reported as real-spec accuracy. The README and reports intentionally distinguish implemented code from unrun experiments.

## Quick start (Windows PowerShell)

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -e ".[dev]"
specqa demo
specqa ask "Which test verifies requirement R-100?" --demo --trace
specqa ask "Which test verifies requirement R-100?" --demo --mode lexical
specqa graph --demo
specqa eval --demo
pytest
```

Optional dependencies:

```powershell
pip install -e ".[pdf]"       # PyMuPDF ingestion
pip install -e ".[dense]"     # sentence-transformers dense retrieval
pip install -e ".[ocr]"       # Tesseract OCR Python wrapper (Tesseract binary also required)
pip install -e ".[parsers]"   # pdfplumber comparison baseline
pip install -e ".[llm]"       # optional local Transformers generation
pip install -e ".[vision]"    # optional ColQwen2.5 page retrieval adapter
```

On first dense-model use, sentence-transformers may need to download a model. If running offline, use `--mode lexical`.

## Ingest an authorised local corpus (recommended for the assignment)

First accept the licence terms on each publisher site and extract the source ZIPs locally. Do not place the PDFs or extracted text in a public repository. Create an optional `corpus_manifest.json` mapping each relative path to a stable document ID and revision:

```json
{
  "usb-pd/USB_PD_R3.2_V1.2.pdf": {"doc_id": "usb_pd_base", "revision": "R3.2 V1.2"},
  "usb4/USB4_Specification_2.0.pdf": {"doc_id": "usb4_base", "revision": "2.0"}
}
```

Then run:

```powershell
specqa ingest-dir "D:\licensed-specs" --manifest "D:\licensed-specs\corpus_manifest.json" --out "data\processed\elements.jsonl" --report "data\processed\ingest_report.json"
```

The batch report lists failed PDFs, duplicate-content groups and element-ID collisions. Exact duplicate files are reported rather than silently removed, because revision identity and licensing context matter. Review the report and validate parser output against source pages before treating the corpus as evaluation-ready. The command does not download files or automatically extract ZIPs.

## Ingest an authorised local PDF

```powershell
specqa ingest "C:\private-specs\example.pdf" --out "data\processed\elements.jsonl" --render-pages "data\private-page-images"
specqa ask "What does this section say about ...?" --elements "data\processed\elements.jsonl" --mode lexical --trace
```

Keep licensed source PDFs, page renders and extracted text out of public repositories. `data/processed/` is ignored by Git; verify your own paths and repository status before publishing. PDF section detection is a heuristic and must be validated against source headings.

## Gold-set validation

Before reporting assignment metrics, validate the source-backed gold set against the ingested corpus. The validator checks question count, duplicate IDs/questions, author/verifier fields, evidence membership, provenance, and whether synthetic fixtures were accidentally used as gold evidence. It does **not** prove factual correctness; a second reviewer must inspect each cited PDF.

```powershell
specqa validate-gold --elements data\processed\elements.jsonl --gold eval\gold.json --minimum-questions 60
```

## Evaluation

`specqa eval --demo` only tests the synthetic fixture. For source-verified data, prepare a JSON gold file with `id`, `question`, `gold_element_ids`, and `category`, then run:

```powershell
specqa eval --elements data/processed/elements.jsonl --gold eval/gold.json --mode lexical
```

Optional local LLM generation (model files must already exist locally unless you explicitly allow downloads):

```powershell
specqa ask "Your engineering question" --elements data\processed\elements.jsonl --mode hybrid --llm-model "C:\models\your-instruct-model" --trace
```

Run parser comparison on the same hand-selected pages with `benchmarks/parsers/compare_parsers.py`; run OCR metric scoring with `benchmarks/ocr/benchmark_metrics.py`. See `CORPUS.md`, `OCR_BENCHMARK.md`, `EVALUATION.md`, `CAPSTONE_ANALYSIS.md`, `DIAGRAMS.md`, `KG_SCHEMA.md`, `TEAM.md` and `docs/FACULTY_REVIEW.md`. Real-corpus OCR/vision/ablation metrics remain pending until the authorised corpus and labelled ground truth are available.
