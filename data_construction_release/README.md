# Data construction code for ICADL 2026

This repository organizes the supplied Python scripts for *Where Are Research Data Published? Identifying Their Publication URLs in Scholarly Papers*. The unchanged files are in `original/`; path-adjusted copies are in `scripts/`. The supplied files **do not form a complete reproduction pipeline**: the PDF-to-MMD converter and the program that creates URL context fields are missing. See `REVIEW_JA.md` before publishing or claiming reproduction of the paper's 17,977 examples.

## Inputs and setup

Run commands from the repository root. Use Python 3.9 or newer (the scripts use built-in generic type hints). Install `pip install -r requirements.txt`. The original software versions are unknown; this file lists direct imports and does not claim to recreate the original environment.

Place the **same PWC archive snapshot used for the experiments**, with the following names, in `data/input/`:

- `datasets_JST202508081105.json`: JSON list with `paper` and/or `verified_paper` objects containing `title`, and dataset `name` and `homepage`.
- `papers-with-abstracts_JST202508081105.json`: JSON list with paper `title`, `date` (`YYYY-MM-DD`), and `url_pdf` (optionally `conference_url_pdf`).

The archive snapshots are not included. No PDF, extracted text, or source dataset is redistributed here. The optional `pt_cs_ci_dict_output.json` is also not included and its producer is not among the supplied files.

## Commands and paper steps

| Paper step | Command | Result and limitation |
| --- | --- | --- |
| 1. Obtain paper/data URL pairs | `python scripts/making_dataset.py` | Writes `data/intermediate/pwc_pairs.csv` from PWC dataset records. This preliminary CSV is **not** the labeled output and is not read by subsequent commands. |
| 2. Download PDFs | `python scripts/01_download_pdfs.py` | Matches unique dataset paper titles to paper records by **bidirectional substring matching** and downloads `url_pdf` into `data/pdf/`. Ambiguous/missing matches and failures go to `data/logs/`. A subsequent run skips existing filenames. This is the source behavior, including its potential for mismatches. |
| 3. Convert PDFs to text | **Missing program** | Supply `.mmd` text files in `data/mmd/`, named by paper title (the filename stem is used as the title in step 4). The converter and its settings cannot be reconstructed from these scripts. |
| 4a. Extract URLs from MMD | `python scripts/02_extract_urls.py` | Writes `data/intermediate/no_kagikakko_extracted_urls.json`, a mapping of filename stem to deduplicated URL list. The regex and `modify_url` logic are unchanged. |
| 4b. Extract surrounding text | **Missing program** | The URL extractor above does **not** output section title, three-sentence context, footnote text, or bibliography. No command in the supplied set creates the JSON consumed by the unfinished diagnostic script. |
| 5. Label URLs | `python scripts/03_label_urls.py` | Uses `scripts/making_dataset_produce_or_not_url_classify.py`; writes `data/intermediate/labelled.csv` with `id,name,homepage,paper_title,label`. See labeling caveats below. |
| Extra. Append publication date | `python scripts/04_add_year.py` | Reads the labeled CSV and paper records, writing `data/intermediate/labelled_with_year.csv` with `id,name,homepage,paper_title,year,label`. The `year` column actually contains the unmodified full `date` string. Rows with no exactly matching paper title are dropped. |

The optional command `python scripts/02b_trim_parentheses_optional.py` writes `perfect_extracted_urls.json` but **does not feed step 5**. It corresponds to a different, unused branch. Do not run it as part of the default sequence.

`scripts/05_context_diagnostic_incomplete.py` reads `data/input/pt_cs_ci_dict_output.json` and the dated CSV, counts title matches, and **does not write the final dataset**. `scripts/06_split_diagnostic_incomplete.py` sorts paper dates, selects the last 10% of papers as a test group, removes a hard-coded list from the remaining group, and prints a balanced sample; the train/dev split and three output CSV writers are commented out. Neither is a finished step of the reproducible pipeline. They are retained for provenance, not run by default.

## Labeling behavior that must be preserved or reviewed

The original classifier lowercases and strips every non-ASCII-alphanumeric character from titles **and URLs** before equality checks. It compares every PWC homepage for a paper to every extracted URL. A matching pair adds the **PWC homepage string** to the positive list. Every nonmatching pair adds the extracted URL to a negative list. It then keeps negative URLs only for papers with at least one positive URL. As a result, records with multiple PWC homepages can contain repeated URLs and can place a matching extracted URL in both classes. The positive CSV joins the **first** matching dataset name by original title and skips empty URL/title values. The scripts here preserve these rules; they do not silently deduplicate or correct labels.

The paper reports 17,977 URL/context pairs, 3,185 positive examples, and a year-based train/development/test split of 13,715/1,635/2,627. Those counts **cannot be verified with the supplied files**. In particular, `labelled.csv` lacks the surrounding text required by the paper, and the provided split script does not write the reported split. The paper describes matching publication URLs, but these scripts implement normalized URL equality, not literal equality. Resolve these differences with the original intermediate data and missing programs before citing this package as an exact reproduction.

## Repository layout

- `original/`: byte-for-byte copies of the nine supplied `.py` files; historical record.
- `scripts/`: same computational logic with local imports/file paths connected. Run from this repository root.
- `data/`: input/output directories ignored by Git apart from placeholders.
- `REVIEW_JA.md`: per-file audit, decisions, and publication checklist in Japanese.

The only intended edits in `scripts/` are file paths, import-compatible filenames, creation of the log directory, and the output argument to the existing URL extraction function. Check changes against `original/` if you modify the scripts further. No license is included because the code owner has not selected one. Cite the paper and the archive snapshot used; add a code license only after confirming rights with the coauthors.
