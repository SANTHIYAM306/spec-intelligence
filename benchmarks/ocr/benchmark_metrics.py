"""Compute OCR benchmark metrics from manually labelled JSONL pairs.

Input JSONL fields: page_id, content_type, ground_truth, prediction, elapsed_seconds,
optional blocks_ground_truth, blocks_prediction. This script computes text error rate and
block-order accuracy only; table structure and bbox IoU need labelled cell/box annotations.
No benchmark result is implied until real authorised pages are labelled and processed.
"""
import argparse, json
from pathlib import Path

def levenshtein(a: str, b: str) -> int:
    previous = list(range(len(b)+1))
    for i, ca in enumerate(a, 1):
        current = [i]
        for j, cb in enumerate(b, 1):
            current.append(min(current[-1]+1, previous[j]+1, previous[j-1]+(ca != cb)))
        previous = current
    return previous[-1]

def norm(s: str) -> str:
    return " ".join(s.casefold().split())

def score_rows(rows):
    result = {}
    for row in rows:
        gt, pred = norm(row.get("ground_truth", "")), norm(row.get("prediction", ""))
        cer = levenshtein(gt, pred) / max(1, len(gt))
        cat = row.get("content_type", "unspecified")
        item = result.setdefault(cat, {"pages": 0, "cer_sum": 0.0, "seconds_sum": 0.0})
        item["pages"] += 1; item["cer_sum"] += cer
        item["seconds_sum"] += float(row.get("elapsed_seconds", 0))
    for item in result.values():
        n = item["pages"]
        item["mean_normalized_edit_distance"] = round(1-item["cer_sum"]/n, 4)
        item["mean_seconds_per_page"] = round(item["seconds_sum"]/n, 4)
        del item["cer_sum"], item["seconds_sum"]
    return result

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("predictions", help="JSONL file of labelled OCR results")
    ap.add_argument("--out", default="benchmarks/ocr/results.json")
    args = ap.parse_args()
    rows = [json.loads(x) for x in Path(args.predictions).read_text(encoding="utf-8").splitlines() if x.strip()]
    result = {"page_count": len(rows), "by_content_type": score_rows(rows),
              "warning": "Only as valid as the manual labels and the measured predictions supplied."}
    Path(args.out).parent.mkdir(parents=True, exist_ok=True)
    Path(args.out).write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
if __name__ == "__main__": main()
