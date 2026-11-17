# Evaluation plan

The assignment requires at least 60 verified questions, approximately 20 held-out reviewer questions, Recall@k/MRR/nDCG, answer correctness, faithfulness, citation accuracy, refusal accuracy, parsing quality, KG precision/duplicate rate, latency and ablations A–F.

## Current executable support
`specqa eval --elements ELEMENTS.jsonl --gold GOLD.json --mode lexical` evaluates retrieval Recall@k and MRR against gold element IDs, plus category slices. `GOLD.json` is a list of objects with `id`, `question`, `gold_element_ids`, and `category`. Do not use the provided synthetic fixture as real evaluation.

## Required next experimental work
- Build and independently verify at least 60 questions from the authorised seven-source corpus; record gold answer, source element IDs, category, author and verifier.
- Keep a held-out set separate from development questions.
- Measure retrieval Recall@k, MRR and nDCG@5; manually inspect a sample of returned evidence.
- Evaluate answer correctness, claim-level faithfulness, citation/page/region accuracy and refusal accuracy. Manually review at least 20% of answer judgments.
- Compare parser choices on the same 20 pages, including table fidelity and reading order.
- Run the fixed ~40-page OCR benchmark and include Unlimited-OCR single-page and multi-page variants when hardware is available.
- Add structured figure evaluation for 10 diagrams and table-cell evaluation for 10 tables.
- Compare configurations A–F exactly as specified by the assignment: A naive dense RAG; B hybrid + reranker; C vision-only; D B+C fused with structured tables/figures; E D+KG; F E+agent planning/reflection/citation verification.
- Report each category separately and do error analysis for every wrong answer. Do not fill results tables with expected or fabricated numbers.

## Current status
Only synthetic-fixture tests and metrics can be run here. Real-corpus scores, OCR benchmark results, vision retrieval results, KG precision and A–F ablations are **not measured**.
