# Data construction code for ICADL 2026

This package organizes the supplied Python scripts for *Where Are Research Data Published? Identifying Their Publication URLs in Scholarly Papers*. The first nine unchanged files are in `original/`; eight additional unchanged files are in `original_additional/`. Both are excluded from Git by default. Runnable and repaired scripts are in `scripts/`. The author confirmed that PDFs were converted to MMD with Nougat. Additional supplied programs parse MMD paragraphs/sentences and TEI XML references, and attach these contexts to labeled URLs. **The exact historical software settings and final split membership have not been established.** Read `REVIEW_JA.md` before claiming reproduction of the published 17,977 examples.

## Put this in a GitHub repository

Clone the **repository** (GitHub's Code tab), unzip this package, and copy the **contents inside** `data_construction_release/` into the clone's root. Keep `README.md` and `.gitignore` at the repository root, alongside `scripts/` and `requirements.txt`. Do not nest the whole package as `repository/data_construction_release/`. `original/` remains available locally for checking, but is ignored by Git. Review `git status` before committing; the PWC archive, PDFs, MMDs, output data, and historical originals must not be staged by the default settings.

## Inputs and setup

Run commands from the repository root. For a WSL/Ubuntu setup from scratch, follow `SETUP_JA.md`. The recommended environment uses Python 3.11 and uv:

```bash
uv python install 3.11
uv venv --python 3.11 --seed
uv pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_trf
```

Run scripts using `.venv/bin/python scripts/<script-name>.py`. Python 3.9 or newer is required by the source syntax. The original software versions are unknown; this file lists direct imports and does not claim to recreate the original environment.

Place the **same PWC archive snapshot used for the experiments**, with the following names, in `data/input/`:

- `datasets_JST202508081105.json`: JSON list with `paper` and/or `verified_paper` objects containing `title`, and dataset `name` and `homepage`.
- `papers-with-abstracts_JST202508081105.json`: JSON list with paper `title`, `date` (`YYYY-MM-DD`), and `url_pdf` (optionally `conference_url_pdf`).

The archive snapshots are not included. No PDF, extracted text, or source dataset is redistributed here. The MMD context parser now generates `pt_cs_ci_dict_output.json` from the `.mmd` files. Reference enrichment also requires TEI XML with `biblStruct` and in-text `ref type="bibr"` elements; the original PDF-to-XML command was not supplied.

## Commands and paper steps

| Paper step | Command | Result and limitation |
| --- | --- | --- |
| 1. Obtain paper/data URL pairs | `python scripts/making_dataset.py` | Writes `data/intermediate/pwc_pairs.csv` from PWC dataset records. This preliminary CSV is **not** the labeled output and is not read by subsequent commands. |
| 2. Download PDFs | `python scripts/01_download_pdfs.py` | Matches unique dataset paper titles to paper records by **bidirectional substring matching** and downloads `url_pdf` into `data/pdf/`. Ambiguous/missing matches and failures go to `data/logs/`. A subsequent run skips existing filenames. This is the source behavior, including its potential for mismatches. |
| 3. Convert PDFs to MMD | `uvx --from nougat-ocr nougat data/pdf -o data/mmd` | Nougat was used according to the author. This is an example using its documented CLI, not a verified historical command. Nougat outputs an `.mmd` with the PDF filename stem. Check the resulting titles and record the actual version/model/options before claiming exact reproduction. |
| 4a. Extract URLs from MMD | `python scripts/02_extract_urls.py` | Writes `data/intermediate/no_kagikakko_extracted_urls.json`, a mapping of filename stem to deduplicated URL list. The regex and `modify_url` logic are unchanged. |
| 4b. Parse MMD context | `DATASET_PARSER_CPU=1 .venv/bin/python scripts/07_parse_mmd_context.py` | Produces `data/intermediate/pt_cs_ci_dict_output.json` with passage titles, paragraphs, one citation sentence, footnote content/type, and extracted URL. Omit `DATASET_PARSER_CPU=1` to require the original GPU mode. This is a path-adjusted copy of the later `parser_footnote.py` revision, with one uninitialized variable repaired. |
| 5. Label URLs | `python scripts/03_label_urls.py` | Uses `scripts/making_dataset_produce_or_not_url_classify.py`; writes `data/intermediate/labelled.csv` with `id,name,homepage,paper_title,label`. See labeling caveats below. |
| Extra. Append publication date | `python scripts/04_add_year.py` | Reads the labeled CSV and paper records, writing `data/intermediate/labelled_with_year.csv` with `id,name,homepage,paper_title,year,label`. The `year` column actually contains the unmodified full `date` string. Rows with no exactly matching paper title are dropped. |
| Reference input (parallel to 4b) | Put full-text TEI files in `data/xml/`; optionally use `scripts/08a_generate_tei_grobid.py` with a running local GROBID service | TEI files should share the corresponding PDF filename stem. GROBID is a **possible adapter**, not a recovered historical setting. |
| Parse TEI references | `DATASET_PARSER_CPU=1 .venv/bin/python scripts/08_parse_tei_references.py` | Produces `data/intermediate/xml_ref_dict.json`, extracting in-text reference contexts linked to bibliography URLs. Requires the spaCy transformer model. |
| Enrich MMD reference records | `.venv/bin/python scripts/09_add_reference_info.py` | Produces `data/intermediate/url_around_info.json` and `reference_merge_report.json` (including unmatched references). Repairs the original comparison of a bibliography string to a URL by comparing the `URL` fields, and avoids appending to the iterated list. |
| Join labeled URLs with occurrences | `.venv/bin/python scripts/10_combine_context.py` | Writes `data/intermediate/dataset_with_context.csv` and `combine_report.json`. Joins titles with an ambiguity check and URLs using the same normalization as the labeler. The original substring join is available with `--url-mode legacy-substring`. Adds a newly reconstructed three-sentence field from the same paragraph; inspect `context_status` in the report. |
| Candidate year split | `.venv/bin/python scripts/11_split_candidate.py` | Writes train/dev/test CSVs and `split_report.json` under `data/intermediate/split_candidate/`. This is a **new chronological paper-grouped candidate**, not the recovered historical split. The report compares row counts to the paper. |
| Audit candidate | `.venv/bin/python scripts/12_validate_outputs.py` | Writes `data/intermediate/validation_report.json`. Fails on broken columns, invalid labels, missing keys, or splits that omit, duplicate, or share papers. Published totals and unmatched contexts are reported for review; different totals do not alone cause failure. |

The optional command `python scripts/02b_trim_parentheses_optional.py` writes `perfect_extracted_urls.json` but **does not feed step 5**. It corresponds to a different, unused branch. Do not run it as part of the default sequence.

`scripts/05_context_diagnostic_incomplete.py` and `scripts/06_split_diagnostic_incomplete.py` remain historical diagnostics and should not be run in the standard pipeline. The eight additional historical files include three statistics-only scripts and an older `parser_footnote_copy.py`; see `REVIEW_JA.md`.

## Labeling behavior that must be preserved or reviewed

The original classifier lowercases and strips every non-ASCII-alphanumeric character from titles **and URLs** before equality checks. It compares every PWC homepage for a paper to every extracted URL. A matching pair adds the **PWC homepage string** to the positive list. Every nonmatching pair adds the extracted URL to a negative list. It then keeps negative URLs only for papers with at least one positive URL. As a result, records with multiple PWC homepages can contain repeated URLs and can place a matching extracted URL in both classes. The positive CSV joins the **first** matching dataset name by original title and skips empty URL/title values. The scripts here preserve these rules; they do not silently deduplicate or correct labels.

The paper reports 17,977 URL/context pairs, 3,185 positives, and train/development/test row counts of 13,715/1,635/2,627. These **cannot be verified without the historical PWC/PDF/MMD/TEI intermediates**. Nougat, spaCy and XML generation settings remain unknown. The original labeler uses normalized URL equality, whereas the original final join used URL substring matching; the repaired join defaults to normalized equality and exposes the legacy behavior as an option. The historical parser stores the one containing sentence and its paragraph; `10_combine_context.py` newly derives the paragraph-local three-sentence context and reports when the containing sentence cannot be found. The supplied split script did not write the reported split. Treat the new split as a candidate until paper membership and counts are checked against historical outputs.

Nougat CLI documentation: https://github.com/facebookresearch/nougat . The example above keeps Nougat's dependencies in a separate uv tool environment; `nougat-ocr` is therefore not added to this repository's `requirements.txt`.

## Repository layout

- `original/`: byte-for-byte copies of the nine supplied `.py` files; local historical record excluded from Git by default.
- `original_additional/`: byte-for-byte copies of the eight later supplied `.py` files; also excluded from Git.
- `scripts/`: same computational logic with local imports/file paths connected. Run from this repository root.
- `data/`: input/output contents ignored by Git apart from directory placeholders.
- `REVIEW_JA.md`: per-file audit, decisions, and publication checklist in Japanese.
- `SETUP_JA.md`: WSL/Ubuntu and uv setup from a clean machine in Japanese.

Scripts `01`–`06` primarily adjust paths and imports from `original/`. Script `07` also fixes an uninitialized footnote variable and allows CPU execution; `08` adjusts paths and CPU selection. Scripts `08a` and `09`–`12` contain new or repaired logic, described above and in `REVIEW_JA.md`. No license is included because the code owner has not selected one. Cite the paper and the archive snapshot used; add a code license only after confirming rights with the coauthors.
