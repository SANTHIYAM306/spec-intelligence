# Parser comparison protocol

Run the same 20 pages, including prose, dense tables, diagrams and test-procedure tables:

```powershell
pip install -e ".[pdf]"
pip install pdfplumber
python benchmarks/parsers/compare_parsers.py "C:\private-specs\one-source.pdf" --pages 12 18 22 35 --out benchmarks/parsers/local-results.json
```

Repeat for enough pages to make 20 total. The script records time, text character count, block/word count and detected table count for PyMuPDF and pdfplumber. These are coverage/runtime proxies only, not accuracy metrics. Hand-label table cells, reading order and expected text for the same pages before comparing fidelity. Keep local result files containing source details private when needed.
