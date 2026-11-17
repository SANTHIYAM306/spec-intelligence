# OCR benchmark protocol (not yet run)

The assignment requires a fixed benchmark of approximately 40 pages across the seven authorised specification sources, with at least 15 manually labelled pages. Required content types include prose, bit-field/message tables, multi-page parameter tables, vector state diagrams, raster Tech 2 figures, and test-procedure tables.

## Reproducible protocol
1. Select pages and record `doc_id`, revision, page number, content type, SHA-256, and why the page is challenging. Keep source PDFs and OCR output private.
2. Manually label ground-truth text, reading order, table cells, and bounding boxes for at least 15 pages.
3. Run each parser on the exact same pages. Include Unlimited-OCR single-page and multi-page runs only on authorised local hardware. Record model revision, GPU, VRAM, RAM, wall time, and command.
4. Save JSONL rows matching `benchmark_metrics.py`: `page_id`, `content_type`, `ground_truth`, `prediction`, `elapsed_seconds`.
5. Run `python benchmarks/ocr/benchmark_metrics.py predictions.jsonl`. Add table cell accuracy/TEDS, block reading-order accuracy, and bounding-box IoU once corresponding labels are available.
6. Report failures by content type. Do not invent numbers if GPU/model access or labels are unavailable.

No OCR benchmark is claimed to have run in this repository yet. `benchmark_metrics.py` is a scoring utility, not benchmark evidence.
