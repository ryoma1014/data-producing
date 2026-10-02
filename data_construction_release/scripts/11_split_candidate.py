"""Create a paper-grouped chronological 8:1:1 candidate split.

This is newly reconstructed. The supplied historical split script did not write
train/dev/test and cannot establish the exact paper membership reported in the
paper. The report states whether this candidate matches published row counts.
"""

import argparse
import csv
import json
from datetime import date
from pathlib import Path


EXPECTED = {"train": 13715, "dev": 1635, "test": 2627}


def split(rows):
    dates = {}
    for row in rows:
        title = row.get("paper_title", "")
        raw_date = row.get("year", "")
        if not title or not raw_date:
            raise ValueError(f"Missing paper title/date at row id {row.get('id')}")
        parsed = date.fromisoformat(raw_date[:10])
        if title in dates and dates[title] != parsed:
            raise ValueError(f"Conflicting publication dates for {title!r}")
        dates[title] = parsed
    titles = sorted(dates, key=lambda title: (dates[title], title))
    n = len(titles)
    if n < 3:
        raise ValueError("At least three distinct papers are needed to split")
    # Last approximately 10% of papers become test, preceding 10% dev.
    n_test = max(1, round(n * 0.1))
    n_dev = max(1, round(n * 0.1))
    groups = {"train": set(titles[:n-n_test-n_dev]),
              "dev": set(titles[n-n_test-n_dev:n-n_test]),
              "test": set(titles[n-n_test:])}
    results = {name: [r for r in rows if r["paper_title"] in group]
               for name, group in groups.items()}
    report = {"method": "chronological paper-grouped candidate, not verified historical membership",
              "total_rows": len(rows), "distinct_papers": n,
              "splits": {name: {"rows": len(results[name]), "papers": len(groups[name]),
                                "positive": sum(r.get("label") == "Produce" for r in results[name]),
                                "earliest_date": str(min(dates[t] for t in groups[name])) if groups[name] else None,
                                "latest_date": str(max(dates[t] for t in groups[name])) if groups[name] else None}
                         for name in groups}}
    report["published_row_counts_match"] = all(
        report["splits"][name]["rows"] == expected for name, expected in EXPECTED.items()
    )
    return results, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", type=Path, default=Path("data/intermediate/dataset_with_context.csv"))
    p.add_argument("--out-dir", type=Path, default=Path("data/intermediate/split_candidate"))
    args = p.parse_args()
    with args.input.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fields = reader.fieldnames
        if not fields:
            raise ValueError("Empty input CSV")
        rows = list(reader)
    results, report = split(rows)
    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, group in results.items():
        with (args.out_dir / f"{name}.csv").open("w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            writer.writerows(group)
    with (args.out_dir / "split_report.json").open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
