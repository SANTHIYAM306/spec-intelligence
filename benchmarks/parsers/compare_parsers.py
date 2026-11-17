"""Compare PyMuPDF and pdfplumber extraction on identical PDF pages.

This measures extraction coverage and runtime only. Fidelity metrics require manually labelled
ground truth; this script intentionally does not fabricate them.
"""
from __future__ import annotations
import argparse, json, statistics, time
from pathlib import Path

def run_pymupdf(pdf: Path, pages: list[int]) -> dict:
    import fitz
    samples=[]
    with fitz.open(pdf) as doc:
        for n in pages:
            page=doc[n-1]; t=time.perf_counter()
            text=page.get_text("text")
            blocks=[b for b in page.get_text("blocks") if len(b)>4 and str(b[4]).strip()]
            samples.append({"page":n,"seconds":time.perf_counter()-t,"chars":len(text),
                            "blocks":len(blocks),"tables":len(page.find_tables().tables) if hasattr(page,"find_tables") else None})
    return {"parser":"PyMuPDF","pages":len(samples),"seconds_median":statistics.median(x["seconds"] for x in samples),
            "chars_total":sum(x["chars"] for x in samples),"blocks_total":sum(x["blocks"] for x in samples),
            "tables_detected_total":sum(x["tables"] or 0 for x in samples),"per_page":samples}

def run_pdfplumber(pdf: Path, pages: list[int]) -> dict:
    import pdfplumber
    samples=[]
    with pdfplumber.open(pdf) as doc:
        for n in pages:
            page=doc.pages[n-1]; t=time.perf_counter()
            text=page.extract_text() or ""
            tables=page.extract_tables() or []
            samples.append({"page":n,"seconds":time.perf_counter()-t,"chars":len(text),
                            "blocks":len(page.extract_words()),"tables":len(tables)})
    return {"parser":"pdfplumber","pages":len(samples),"seconds_median":statistics.median(x["seconds"] for x in samples),
            "chars_total":sum(x["chars"] for x in samples),"blocks_total":sum(x["blocks"] for x in samples),
            "tables_detected_total":sum(x["tables"] for x in samples),"per_page":samples}

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("--pages", nargs="+", type=int, required=True)
    ap.add_argument("--out", default="benchmarks/parsers/results.json")
    args=ap.parse_args(); pdf=Path(args.pdf)
    if not pdf.is_file(): raise SystemExit(f"PDF not found: {pdf}")
    results=[]
    for name, fn in (("PyMuPDF",run_pymupdf),("pdfplumber",run_pdfplumber)):
        try: results.append(fn(pdf,args.pages))
        except ImportError as exc: results.append({"parser":name,"status":"blocked","reason":str(exc)})
    output={"pdf_name":pdf.name,"pages":args.pages,"results":results,
            "warning":"Coverage/speed diagnostics only; no fidelity or correctness score without hand-labelled ground truth."}
    out=Path(args.out); out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(output,indent=2),encoding="utf-8"); print(json.dumps(output,indent=2))
if __name__=="__main__": main()
