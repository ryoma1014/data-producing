"""Optional PDF-to-TEI adapter for a running local GROBID service.

The original XML generation command was not supplied. This adapter produces
the TEI format expected by 08_parse_tei_references.py but is not a claim about
the exact historical GROBID configuration.
"""

import argparse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import requests


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--pdf-dir", type=Path, default=Path("data/pdf"))
    p.add_argument("--xml-dir", type=Path, default=Path("data/xml"))
    p.add_argument("--endpoint", default="http://localhost:8070/api/processFulltextDocument")
    p.add_argument("--overwrite", action="store_true")
    args = p.parse_args()
    args.xml_dir.mkdir(parents=True, exist_ok=True)
    report = {"processed": [], "skipped_existing": [], "failed": []}
    for pdf in sorted(args.pdf_dir.glob("*.pdf")):
        target = args.xml_dir / (pdf.stem + ".xml")
        if target.exists() and not args.overwrite:
            report["skipped_existing"].append(pdf.name)
            continue
        try:
            with pdf.open("rb") as f:
                response = requests.post(args.endpoint,
                                         files={"input": (pdf.name, f, "application/pdf")},
                                         timeout=300)
            response.raise_for_status()
            root = ET.fromstring(response.content)
            if not root.tag.endswith("TEI"):
                raise ValueError(f"Unexpected XML root: {root.tag}")
            target.write_bytes(response.content)
            report["processed"].append(pdf.name)
        except (requests.RequestException, ET.ParseError, ValueError) as exc:
            report["failed"].append({"pdf": pdf.name, "error": str(exc)})
    print(json.dumps(report, ensure_ascii=False, indent=2))
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
