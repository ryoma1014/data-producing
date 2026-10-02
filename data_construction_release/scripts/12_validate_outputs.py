"""Audit the assembled candidate against structural rules and published totals.

Structural errors cause a nonzero exit status. Published totals are reported for
comparison because the exact historical inputs and split are unavailable.
"""

import argparse
import csv
import json
from collections import Counter
from pathlib import Path


PUBLISHED = {"all": 17977, "positive": 3185,
             "train": 13715, "dev": 1635, "test": 2627}
REQUIRED = {"id", "paper_title", "homepage", "year", "label", "Passage-title",
            "Citation-sentence", "Citation-paragraph", "Citation-type",
            "Context-three-sentences", "Source-URL"}


def read_csv(path):
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames:
            raise ValueError(f"Empty CSV: {path}")
        return reader.fieldnames, list(reader)


def audit(all_fields, rows, splits, combine_report):
    errors = []
    missing = sorted(REQUIRED - set(all_fields))
    if missing:
        errors.append(f"Missing CSV columns: {missing}")
    if not rows:
        errors.append("No dataset occurrences were produced")
    labels = Counter(row.get("label", "") for row in rows)
    if set(labels) - {"Produce", "nonProduce"}:
        errors.append(f"Unexpected label values: {sorted(set(labels) - {'Produce', 'nonProduce'})}")
    if any(not row.get("paper_title") or not row.get("homepage") or not row.get("Source-URL")
           for row in rows):
        errors.append("At least one row lacks title, homepage, or extracted URL")
    actual = {"all": len(rows), "positive": labels["Produce"]}
    if splits is not None:
        for name, (fields, part) in splits.items():
            actual[name] = len(part)
            if fields != all_fields:
                errors.append(f"{name}.csv columns differ from the combined CSV")
        # Counter retains duplicate occurrences, unlike a set of IDs or URLs.
        fingerprint = lambda row: tuple(row.get(key, "") for key in all_fields)
        original = Counter(map(fingerprint, rows))
        assembled = Counter(fingerprint(row) for _, part in splits.values() for row in part)
        if original != assembled:
            errors.append("Split rows do not exactly partition the combined CSV")
        papers = {name: {row["paper_title"] for row in part}
                  for name, (_, part) in splits.items()}
        if any(papers[a] & papers[b] for a, b in (("train", "dev"), ("train", "test"), ("dev", "test"))):
            errors.append("A paper appears in multiple splits")
    if combine_report is not None and combine_report.get("output_occurrences") != len(rows):
        errors.append("combine_report.json occurrence count differs from CSV")
    return {"structural_errors": errors, "actual_counts": actual,
            "published_counts": PUBLISHED,
            "published_counts_match": {k: actual.get(k) == v for k, v in PUBLISHED.items()},
            "label_counts": dict(labels),
            "combine_unmatched_title_rows": len(combine_report.get("unmatched_title_rows", [])) if combine_report else None,
            "combine_unmatched_url_rows": len(combine_report.get("unmatched_url_rows", [])) if combine_report else None,
            "context_status": combine_report.get("context_status", {}) if combine_report else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--combined", type=Path, default=Path("data/intermediate/dataset_with_context.csv"))
    parser.add_argument("--split-dir", type=Path, default=Path("data/intermediate/split_candidate"))
    parser.add_argument("--combine-report", type=Path, default=Path("data/intermediate/combine_report.json"))
    parser.add_argument("--report", type=Path, default=Path("data/intermediate/validation_report.json"))
    args = parser.parse_args()
    fields, rows = read_csv(args.combined)
    splits = {name: read_csv(args.split_dir / f"{name}.csv") for name in ("train", "dev", "test")}
    with args.combine_report.open(encoding="utf-8") as stream:
        combine_report = json.load(stream)
    result = audit(fields, rows, splits, combine_report)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result["structural_errors"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
