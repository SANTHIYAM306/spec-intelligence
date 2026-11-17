# WS5 exploration — evaluation and integration

## Question
How can the team tell whether each added component improves answers instead of merely adding complexity?

## Approach
Keep one versioned, manually verified gold set and use it for every configuration. Split development and held-out questions. Report Recall@k, MRR, nDCG@5, answer correctness, faithfulness, citation accuracy, refusal accuracy, parser quality, KG precision, latency and resources.

## Current implementation
`evaluation.py` supports retrieval metrics against a user-provided gold JSON; `metrics.py` includes Recall@k, MRR and nDCG@k; `benchmarks/ocr/benchmark_metrics.py` scores labelled OCR output. The ablation helper explicitly marks unavailable model paths as blocked.

## Limitations
No real source corpus or gold set is bundled. Synthetic fixture metrics must never be presented as assignment results. The OCR script currently computes normalized text similarity and elapsed time only; table structure, reading order and bbox metrics need dedicated labels and scorers.
