# WS1 exploration — document AI and OCR

## Question
Which parser/OCR path preserves text order, table cells, diagrams and page regions on the seven specification sources?

## Candidates
1. PyMuPDF block extraction plus best-effort `find_tables`: lightweight and fast for selectable text, but weak on complex layouts and multi-page table stitching.
2. Docling or Marker: layout-aware alternatives to benchmark on the same fixed pages.
3. Unlimited-OCR single-page and multi-page: required by the assignment, GPU/model availability permitting.
4. Tesseract: optional fallback for scanned pages; not a substitute for the required Unlimited-OCR comparison.

## Reproducible experiment required
Select the same ~40 pages across all seven sources; manually label text, cell structure and reading order for at least 15 pages. Measure normalized edit distance/CER, table cell accuracy/TEDS, reading order, element type, bbox IoU, page latency, throughput, RAM/VRAM, and long-horizon behavior at 1/5/10/20+ pages. Record failures and page IDs.

## Current recommendation
Use PyMuPDF as the baseline parser and preserve source provenance. Route empty-text pages to OCR. Decide whether Unlimited-OCR should be global or selective only after the benchmark. No comparative measurements have been made in this repository.
