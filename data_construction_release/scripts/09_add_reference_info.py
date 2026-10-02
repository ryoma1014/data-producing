"""Join TEI reference contexts to MMD contexts without mutating the iterated list.

This is a repaired implementation of original_additional/add_ref_info.py.
The original compared XML Citation-info (a bibliography dictionary rendered as a
string) to an MMD URL, then appended to the same list being iterated. Neither
operation can reliably produce the intended one-record-per-citation result.
"""

import argparse
import json
import re
from pathlib import Path


def normalized_title(value):
    return re.sub(r"[^A-Za-z0-9]", "", value or "").lower()


def title_index(mapping):
    index = {}
    for title in mapping:
        key = normalized_title(title)
        if key in index and index[key] != title:
            raise ValueError(f"Ambiguous normalized title: {index[key]!r}, {title!r}")
        index[key] = title
    return index


def enrich(mmd, xml):
    result = {title: [dict(row) for row in rows] for title, rows in mmd.items()}
    xml_index = title_index(xml)
    report = {"mmd_papers": len(mmd), "xml_papers": len(xml), "matched_papers": 0,
              "matched_contexts": 0, "extra_reference_occurrences": 0,
              "xml_papers_without_mmd": [], "unmatched_reference_contexts": []}
    used_xml = set()
    for title, rows in result.items():
        xml_title = title if title in xml else xml_index.get(normalized_title(title))
        if xml_title is None:
            for row in rows:
                if row.get("Citation-type") == "Reference":
                    report["unmatched_reference_contexts"].append({"paper_title": title, "URL": row.get("URL", "")})
            continue
        used_xml.add(xml_title)
        report["matched_papers"] += 1
        by_url = {}
        for ref in xml[xml_title]:
            if ref.get("URL"):
                by_url.setdefault(ref["URL"], []).append(ref)
        extras = []
        for row in rows:  # snapshot of the input: never iterate appended records
            if row.get("Citation-type") != "Reference":
                continue
            matches = by_url.get(row.get("URL", ""), [])
            if not matches:
                report["unmatched_reference_contexts"].append({"paper_title": title, "URL": row.get("URL", "")})
                continue
            report["matched_contexts"] += 1
            for number, ref in enumerate(matches):
                target = row if number == 0 else dict(row)
                target["Citation-paragraph"] = ref.get("Citation-paragraph", "")
                target["Citation-sentence"] = ref.get("Citation-sentence", "")
                target["Passage-title"] = ref.get("Paragraph-title", [])
                target["Citation-info"] = ref.get("Citation-info", "")
                target["Citation-type"] = ref.get("Citation-type", "Reference")
                if number:
                    extras.append(target)
                    report["extra_reference_occurrences"] += 1
        rows.extend(extras)
    report["xml_papers_without_mmd"] = sorted(set(xml) - used_xml)
    return result, report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--mmd", type=Path, default=Path("data/intermediate/pt_cs_ci_dict_output.json"))
    p.add_argument("--xml", type=Path, default=Path("data/intermediate/xml_ref_dict.json"))
    p.add_argument("--out", type=Path, default=Path("data/intermediate/url_around_info.json"))
    p.add_argument("--report", type=Path, default=Path("data/intermediate/reference_merge_report.json"))
    args = p.parse_args()
    with args.mmd.open(encoding="utf-8") as f:
        mmd = json.load(f)
    with args.xml.open(encoding="utf-8") as f:
        xml = json.load(f)
    result, report = enrich(mmd, xml)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(json.dumps({k: len(v) if isinstance(v, list) else v for k, v in report.items()}, ensure_ascii=False))
    print(f"Saved: {args.out}; inspect {args.report}")


if __name__ == "__main__":
    main()
