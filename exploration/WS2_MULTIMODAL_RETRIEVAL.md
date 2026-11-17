# WS2 exploration — multimodal retrieval

## Question
Which chunking, embedding, lexical, reranking and page-image strategy best serves identifier-heavy and figure questions?

## Candidates
- BM25-style lexical retrieval: exact identifiers, timers, test IDs and table labels.
- Sentence-transformer dense retrieval: paraphrases and semantic questions.
- Hybrid BM25+dense with RRF; optional cross-encoder reranking.
- ColQwen2.5/ColPali page retrieval with late interaction/MaxSim for layout-heavy figures.

## Current implementation
`chunking.py` creates parent-linked chunks while keeping tables and figures atomic. `retrieval.py` offers lexical search, optional dense search, RRF and optional cross-encoder reranking. `vision.py` renders page images and provides a ColQwen adapter plus a tested MaxSim primitive.

## Required experiment
Use one verified gold set across A/B/C/D. Report Recall@k, MRR, nDCG@5, latency, storage per page and content-type breakdown. Do not treat a rendered image or the MaxSim primitive as a trained vision index. No real-corpus experiment has been run yet.
