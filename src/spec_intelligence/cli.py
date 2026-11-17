"""CLI for ingestion, chunking, graph export, evidence QA, and evaluation."""
from __future__ import annotations
import argparse, json, logging
from pathlib import Path
from typing import Any
from .agent import run_agent
from .corpus import DEMO_RECORDS, load_jsonl, write_jsonl
from .evaluation import evaluate, evaluate_gold
from .graph import build_graph, graph_query, graph_statistics
from .ingest import ingest_pdf
from .chunking import chunk_elements
from .vision import render_pdf_pages
from .ocr import ocr_image

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")

def _records(args: argparse.Namespace) -> list[dict[str, Any]]:
    if getattr(args, "demo", False): return DEMO_RECORDS
    path = getattr(args, "elements", None)
    if path: return load_jsonl(path)
    raise ValueError("Select --demo or provide --elements PATH")

def main() -> None:
    parser = argparse.ArgumentParser(prog="specqa", description="Evidence-grounded technical specification QA")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("demo", help="run synthetic end-to-end demo")
    ask = sub.add_parser("ask", help="run bounded agent workflow")
    ask.add_argument("question"); ask.add_argument("--demo", action="store_true")
    ask.add_argument("--elements"); ask.add_argument("-k", type=int, default=6)
    ask.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="hybrid")
    ask.add_argument("--rerank", action="store_true"); ask.add_argument("--trace", action="store_true")
    ask.add_argument("--max-steps", type=int, default=7); ask.add_argument("--min-score", type=float, default=0.2)
    ask.add_argument("--page-index", help="JSON manifest from `specqa render` for optional ColQwen page search")
    ask.add_argument("--llm-model", help="optional local Transformers model path; no download by default")
    ask.add_argument("--allow-model-download", action="store_true", help="allow Transformers to download the selected model")
    ask.add_argument("--doc", action="append", dest="docs"); ask.add_argument("--revision")
    ask.add_argument("--type", action="append", dest="types")
    ingest = sub.add_parser("ingest", help="extract text blocks/tables from a selectable-text PDF")
    ingest.add_argument("pdf"); ingest.add_argument("--out", default="data/processed/elements.jsonl")
    ingest.add_argument("--render-pages", help="optional directory to render page images")
    ingest.add_argument("--no-tables", action="store_true")
    ingest.add_argument("--revision", default="unknown"); ingest.add_argument("--doc-id")
    batch = sub.add_parser("ingest-dir", help="recursively ingest locally authorised PDFs")
    batch.add_argument("directory"); batch.add_argument("--out", default="data/processed/elements.jsonl")
    batch.add_argument("--report", default="data/processed/ingest_report.json")
    batch.add_argument("--manifest", help="optional JSON mapping relative PDF paths to doc_id/revision")
    batch.add_argument("--render-pages-dir", help="optional root directory for page renders")
    batch.add_argument("--no-tables", action="store_true")
    chunk = sub.add_parser("chunk", help="create structure-aware parent/child chunks")
    chunk.add_argument("--elements", required=True); chunk.add_argument("--out", default="data/processed/chunks.jsonl")
    chunk.add_argument("--max-chars", type=int, default=1400); chunk.add_argument("--overlap", type=int, default=120)
    stitch = sub.add_parser("stitch-tables", help="add conservative adjacent-page table continuation candidates")
    stitch.add_argument("--elements", required=True); stitch.add_argument("--out", default="data/processed/elements_with_stitched_tables.jsonl")
    render = sub.add_parser("render", help="render PDF pages for optional vision indexing")
    render.add_argument("pdf"); render.add_argument("--out", default="data/processed/page_images")
    render.add_argument("--dpi", type=int, default=165); render.add_argument("--pages", nargs="*", type=int)
    ocr = sub.add_parser("ocr", help="run optional Tesseract OCR on a rendered page image")
    ocr.add_argument("image"); ocr.add_argument("--doc-id", required=True); ocr.add_argument("--page", type=int, required=True)
    ocr.add_argument("--revision", default="unknown"); ocr.add_argument("--out", default="data/processed/ocr.jsonl")
    graph = sub.add_parser("graph", help="build graph, print stats, and export JSON")
    graph.add_argument("--demo", action="store_true"); graph.add_argument("--elements")
    graph.add_argument("--query"); graph.add_argument("--out", default="data/processed/knowledge_graph.json")
    ev = sub.add_parser("eval", help="evaluate a gold set or run synthetic demo metrics")
    ev.add_argument("--demo", action="store_true"); ev.add_argument("--elements")
    ev.add_argument("--gold", help="JSON list: id, question, gold_element_ids, category")
    ev.add_argument("--mode", choices=["lexical", "dense", "hybrid"], default="lexical")
    validate_gold = sub.add_parser("validate-gold", help="validate gold-set completeness and evidence IDs")
    validate_gold.add_argument("--elements", required=True); validate_gold.add_argument("--gold", required=True)
    validate_gold.add_argument("--minimum-questions", type=int, default=60)
    ab = sub.add_parser("ablate", help="run available configurations and mark unavailable paths as blocked")
    ab.add_argument("--elements", required=True); ab.add_argument("--gold", required=True)
    ab.add_argument("--out", default="data/processed/ablation_report.json"); ab.add_argument("-k", type=int, default=5)
    args = parser.parse_args()
    try:
        if args.command == "ingest-dir":
            from .batch_ingest import ingest_directory
            result = ingest_directory(args.directory, args.out, args.report, args.manifest,
                                      include_tables=not args.no_tables, render_pages_dir=args.render_pages_dir)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == "ingest":
            records = ingest_pdf(args.pdf, args.out, include_tables=not args.no_tables,
                                 render_pages_to=args.render_pages, revision=args.revision, doc_id=args.doc_id)
            counts = {}
            for r in records: counts[r["element_type"]] = counts.get(r["element_type"], 0) + 1
            print(json.dumps({"pdf": args.pdf, "elements": len(records), "types": counts, "output": args.out}, indent=2))
        elif args.command == "stitch-tables":
            from .tables import stitch_table_continuations
            records = load_jsonl(args.elements)
            stitched = stitch_table_continuations(records)
            write_jsonl(records + stitched, args.out)
            print(json.dumps({"input_elements": len(records), "stitched_table_candidates": len(stitched),
                              "out": args.out, "warning": "Inspect every stitched candidate against original pages."}, indent=2))
        elif args.command == "render":
            from .vision import render_pdf_pages
            print(json.dumps(render_pdf_pages(args.pdf, args.out, args.dpi, args.pages), indent=2))
        elif args.command == "ocr":
            rows = ocr_image(args.image, args.doc_id, args.page, args.revision)
            write_jsonl(rows, args.out); print(json.dumps({"lines": len(rows), "out": args.out}, indent=2))
        elif args.command == "chunk":
            rows = chunk_elements(load_jsonl(args.elements), args.max_chars, args.overlap)
            write_jsonl(rows, args.out); print(json.dumps({"chunks": len(rows), "out": args.out}, indent=2))
        elif args.command == "demo":
            result = run_agent("Which test verifies requirement R-100?", DEMO_RECORDS, retrieval_mode="lexical")
            print("SPEC INTELLIGENCE — SYNTHETIC DEMO\n"); print(result["answer"])
            print("\nTrace:", json.dumps(result["trace"], indent=2))
            print("\nAll fixture records are synthetic; no USB values are represented.")
        elif args.command == "ask":
            records = _records(args)
            if args.docs: records = [r for r in records if r.get("doc_id") in args.docs]
            if args.revision: records = [r for r in records if r.get("revision") == args.revision]
            if args.types: records = [r for r in records if r.get("element_type") in args.types]
            page_index = json.loads(Path(args.page_index).read_text(encoding="utf-8")) if args.page_index else None
            result = run_agent(args.question, records, k=args.k, retrieval_mode=args.mode, rerank=args.rerank,
                               max_steps=args.max_steps, min_score=args.min_score, llm_model=args.llm_model,
                               local_files_only=not args.allow_model_download, page_index=page_index)
            if not args.trace: result.pop("trace", None)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == "graph":
            records = _records(args); result = build_graph(records)
            if args.query: result = graph_query(result, args.query)
            else: result["statistics"] = graph_statistics(result)
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"out": args.out, "result": result}, indent=2, ensure_ascii=False))
        elif args.command == "eval":
            records = _records(args)
            if args.gold:
                gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
                result = evaluate_gold(records, gold, retrieval_mode=args.mode)
            else: result = evaluate(records)
            print(json.dumps(result, indent=2, ensure_ascii=False))
        elif args.command == "validate-gold":
            from .gold import validate_gold_set
            records = load_jsonl(args.elements)
            gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
            if not isinstance(gold, list): raise ValueError("Gold file must be a JSON list")
            report = validate_gold_set(gold, records, args.minimum_questions)
            print(json.dumps(report, indent=2, ensure_ascii=False))
            if not report["valid"]: raise SystemExit(2)
        elif args.command == "ablate":
            from .ablation import run_ablation_suite
            records = load_jsonl(args.elements)
            gold = json.loads(Path(args.gold).read_text(encoding="utf-8"))
            result = run_ablation_suite(records, gold, k=args.k)
            Path(args.out).parent.mkdir(parents=True, exist_ok=True)
            Path(args.out).write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
            print(json.dumps({"out": args.out, "result": result}, indent=2, ensure_ascii=False))
    except (ValueError, RuntimeError, OSError, json.JSONDecodeError) as exc:
        logging.error("%s", exc); raise SystemExit(2) from exc

if __name__ == "__main__": main()
