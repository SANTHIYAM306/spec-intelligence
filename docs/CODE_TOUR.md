# Code tour and viva notes

## Follow one question through the system
1. `cli.py` parses `specqa ask`, loads JSONL records and calls `run_agent`.
2. `agent.py::plan_question` assigns a question type; `search` retrieves evidence; `build_graph` and `graph_query` provide candidate relationship context; the trace records each step. If the first retrieval is empty, reflection attempts one identifier-based lexical correction when the step budget permits.
3. `retrieval.py::lexical_search` ranks exact identifier and term matches. If `sentence-transformers` is installed, `dense_search` embeds the query and elements and cosine similarity ranks them. `reciprocal_rank_fusion` merges rankings by element ID.
4. `answer.py` formats evidence excerpts with `[document, revision, section, page, element]` citations. It declines when there is no sufficient retrieved evidence. This baseline intentionally does not invent synthesis.
5. `evaluation.py` calculates retrieval Recall@k and MRR against supplied gold element IDs. A gold set is only valid after the expected IDs and answers are checked against source PDFs.
6. `ingest.py` extracts text blocks and best-effort tables, stores page and bounding-box provenance, optionally renders pages/extracts embedded images, and can run Tesseract on pages with no selectable text.

## Core concepts in plain language
- **Provenance:** every element and graph edge records where it came from so a reviewer can return to the page.
- **BM25-style search:** ranks documents using query-term frequency and rarity; good for exact IDs, less good for paraphrases.
- **Dense retrieval:** maps text to vectors and compares semantic similarity; can retrieve paraphrases, but may miss exact identifiers.
- **Hybrid search:** combines both strengths. Reciprocal Rank Fusion combines ranks without requiring lexical and cosine scores to share a numeric scale.
- **Knowledge graph:** nodes represent entities such as test cases, timers and states; edges represent relations. Provenance on each edge lets the user inspect its source.
- **Agent loop:** plans the question, uses tools, checks evidence, and either returns supported evidence or declines.
- **RAG:** retrieval-augmented generation grounds a response in retrieved source passages instead of model memory. This repository defaults to evidence excerpts. An optional local Transformers model can synthesize JSON claims, but it is not required and was not model-tested in this environment.
- **Refusal:** a correct system says “not found” when the corpus lacks evidence; the assignment's Wi-Fi 7 example is an explicit out-of-corpus test.

## Honest status statement for a review
“This repository has a runnable CLI, tests, page-aware PDF text/table ingestion, lexical retrieval, optional semantic dense retrieval, rank fusion, candidate graph extraction, and a bounded traceable evidence workflow. It is not yet validated against the seven real source groups. Unlimited-OCR, vision-native MaxSim retrieval, verified real-spec gold questions and full A–F ablations remain unmeasured.”
