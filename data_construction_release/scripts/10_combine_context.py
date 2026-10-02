"""Combine labeled paper-URL rows with occurrences from the MMD/TEI parsers.

The historical combine_csv_url_info.py was used as the structural reference.
This version fixes its nested CSV header and reports every unmatched row.
"""

import argparse
import csv
import json
import re
from pathlib import Path


CONTEXT_FIELDS = ["Passage-title", "Citation-sentence", "Citation-info",
                  "Citation-paragraph", "Citation-type", "Context-three-sentences"]
TAGS = re.compile(r"\[Cite(?:_Ref|_Footnote_\d+)?\]")


def norm(value):
    # The classifier uses this equality rule. Keep the same URL comparison here.
    return re.sub(r"[^A-Za-z0-9]", "", value or "").lower()


def index_titles(mapping):
    index = {}
    for title in mapping:
        key = norm(title)
        if key in index and index[key] != title:
            raise ValueError(f"Ambiguous normalized title: {index[key]!r}, {title!r}")
        index[key] = title
    return index


def three_sentences(record, nlp):
    """Get the matched sentence and its neighbors from the same paragraph.

    This is a reconstruction of the paper's described feature, not a recovered
    historical implementation. Return a status if the exact sentence is missing.
    """
    paragraph = record.get("Citation-paragraph", "") or ""
    target = record.get("Citation-sentence", "") or ""
    if not paragraph or not target:
        return target, "missing_paragraph_or_sentence"
    sentences = [s.text.strip() for s in nlp(paragraph).sents if s.text.strip()]
    if not sentences:
        return target, "no_sentences"
    clean_target = " ".join(TAGS.sub("", target).split())
    for i, sentence in enumerate(sentences):
        clean_sentence = " ".join(TAGS.sub("", sentence).split())
        if clean_target == clean_sentence or (clean_target and clean_target in clean_sentence):
            return " ".join(sentences[max(0, i-1):min(len(sentences), i+2)]), "matched"
    return target, "sentence_not_found_in_paragraph"


def combine(labels, contexts, nlp=None, url_mode="normalized"):
    if url_mode not in ("normalized", "exact", "legacy-substring"):
        raise ValueError(f"Unsupported URL matching: {url_mode}")
    title_map = index_titles(contexts)
    output = []
    report = {"labeled_rows": len(labels), "matched_labeled_rows": 0,
              "output_occurrences": 0, "unmatched_title_rows": [],
              "unmatched_url_rows": [], "context_status": {},
              "url_mode": url_mode}
    for label in labels:
        title = label.get("paper_title", "")
        context_title = title if title in contexts else title_map.get(norm(title))
        if context_title is None:
            report["unmatched_title_rows"].append({"id": label.get("id"), "paper_title": title})
            continue
        expected = label.get("homepage", "")
        matches = []
        for context in contexts[context_title]:
            actual = context.get("URL", "")
            if not actual or not expected:
                continue
            if (url_mode == "normalized" and norm(expected) == norm(actual)) or (
                url_mode == "exact" and expected == actual) or (
                url_mode == "legacy-substring" and expected in actual
            ):
                matches.append(context)
        if not matches:
            report["unmatched_url_rows"].append({"id": label.get("id"),
                                                 "paper_title": title, "homepage": expected})
            continue
        report["matched_labeled_rows"] += 1
        for context in matches:
            row = dict(label)
            row["Passage-title"] = json.dumps(context.get("Passage-title", []), ensure_ascii=False)
            for key in ("Citation-sentence", "Citation-info", "Citation-paragraph", "Citation-type"):
                row[key] = context.get(key, "")
            row["Source-URL"] = context.get("URL", "")
            if nlp is None:
                row["Context-three-sentences"] = ""
                status = "not_computed"
            else:
                row["Context-three-sentences"], status = three_sentences(context, nlp)
            report["context_status"][status] = report["context_status"].get(status, 0) + 1
            output.append(row)
    report["output_occurrences"] = len(output)
    return output, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--labels", type=Path, default=Path("data/intermediate/labelled_with_year.csv"))
    p.add_argument("--contexts", type=Path, default=Path("data/intermediate/url_around_info.json"))
    p.add_argument("--out", type=Path, default=Path("data/intermediate/dataset_with_context.csv"))
    p.add_argument("--report", type=Path, default=Path("data/intermediate/combine_report.json"))
    p.add_argument("--url-mode", choices=("normalized", "exact", "legacy-substring"), default="normalized")
    p.add_argument("--skip-three-sentences", action="store_true", help="For a structural dry run only")
    args = p.parse_args()
    with args.labels.open(newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        label_fields = reader.fieldnames
        if not label_fields:
            raise ValueError("The labeled CSV is empty")
        labels = list(reader)
    with args.contexts.open(encoding="utf-8") as f:
        contexts = json.load(f)
    nlp = None
    if not args.skip_three_sentences:
        import spacy
        nlp = spacy.load("en_core_web_trf")
    result, report = combine(labels, contexts, nlp=nlp, url_mode=args.url_mode)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=label_fields + CONTEXT_FIELDS + ["Source-URL"])
        writer.writeheader()
        writer.writerows(result)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: v if not isinstance(v, list) else len(v) for k, v in report.items()}, ensure_ascii=False))
    print(f"Saved: {args.out}; inspect unmatched rows in {args.report}")


if __name__ == "__main__":
    main()
