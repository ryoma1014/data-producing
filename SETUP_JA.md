# WSL（Ubuntu）でゼロから準備する手順

この手順はWSLのUbuntu上で実行する。PowerShellではなく、Ubuntuのターミナルを使う。既存の作業フォルダにGitの履歴衝突がある場合も、新しい場所へcloneするとその履歴を変更せずに準備できる。

## 1. Git、curl、unzipを確認

```bash
git --version
curl --version
unzip -v
```

不足している場合のみ、Ubuntuで `sudo apt update` と `sudo apt install git curl unzip` を実行する。

## 2. uvを導入

公式のインストール方法:

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

インストーラの案内に従ってシェルを開き直し、`uv --version`で確認する。`uv`が見つからない場合は、新しいUbuntuターミナルを起動して再確認する。uv自体の導入にPythonの事前インストールは不要。

## 3. GitHubリポジトリを新しいフォルダにclone

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/ryoma1014/2025-0829-making_dataset.git
cd 2025-0829-making_dataset
```

このURLは相談中に示されたリポジトリ名。別のリポジトリを使う場合はGitHubの「Code」からURLをコピーして置き換える。すでに同名フォルダがある場合は、別の作業場所を選ぶ。作業中は `pwd` でリポジトリ直下にいることを確認する。

## 4. 整理済みZIPの中身を配置

`data_construction_release.zip`をダウンロードし展開する。**ZIP内の `data_construction_release/` の中身**をclone先の直下にコピーする。最終的にclone先の直下に `README.md`、`requirements.txt`、`.gitignore`、`scripts/`、`data/`がある構成にする。

WSLからWindowsのダウンロードフォルダを探す場合は `ls /mnt/c/Users/*/Downloads/data_construction_release.zip` で確認できる。ZIPがすでにWSL内にある場合はその場所を使う。コピー時に既存のREADMEと重なるなら内容を確認する。

コマンドで展開する場合は、以下の `＜Windowsユーザー名＞` を実際の名前に置き換え、clone先のリポジトリ直下で実行する。

```bash
unzip -q '/mnt/c/Users/＜Windowsユーザー名＞/Downloads/data_construction_release.zip' -d ~/projects/package_extract
cp -a ~/projects/package_extract/data_construction_release/. .
```

ZIPを別の場所に保存した場合は、1行目を実際のZIPのパスに置き換える。

## 5. uvでPythonと仮想環境を作る

リポジトリ直下で実行する:

```bash
uv python install 3.11
uv venv --python 3.11 --seed
uv pip install -r requirements.txt
.venv/bin/python -m spacy download en_core_web_trf
.venv/bin/python --version
```

`uv python install`でPython本体を、`uv venv --seed`でこのリポジトリ専用の `.venv/` とモデル導入に必要なpipを用意する。`uv pip install`は依存ライブラリを入れ、最後のコマンドで原コードが読み込むspaCyの`en_core_web_trf`モデルを導入する。`.venv/`はGitから除外してある。実験当時の厳密なライブラリ・モデルのバージョンは不明。

以後、仮想環境の有効化を省くなら、常に `.venv/bin/python` で実行する。ターミナルで `source .venv/bin/activate` を実行し、その後 `python` を使うこともできる。ターミナルを閉じると有効化は解除される。

## 6. PWC入力を配置

以下の**実験で使ったPWCスナップショット**を `data/input/` に置く。ZIPには入っていない。

- `datasets_JST202508081105.json`
- `papers-with-abstracts_JST202508081105.json`

配置後、`ls data/input/`でファイル名を確認する。これらがなければ次のコマンドは実行できない。

## 7. 実行可能な段階を順に動かす

```bash
.venv/bin/python scripts/making_dataset.py
.venv/bin/python scripts/01_download_pdfs.py
```

この時点で `data/intermediate/pwc_pairs.csv` と、取得できたPDFが `data/pdf/` にできる。PDF→`.mmd`の変換にはNougatを使用したことが分かった。公式CLIに沿った実行例は以下（uvxは別のツール環境でNougatを動かす）。

```bash
uvx --from nougat-ocr nougat data/pdf -o data/mmd
ls data/mmd/*.mmd
```

NougatはPDF名と同じstemの`.mmd`を出力する。`02_extract_urls.py`と後述の周辺情報抽出はそのstemを論文タイトルのキーとして使うため、ファイル名を確認する。これは**当時の正確な変換コマンドを再現したものではない**。使用したNougatのバージョン、モデル、オプションは未確認であり、実験時の値が分かればそれに合わせる。Nougat公式: https://github.com/facebookresearch/nougat 。`.mmd`がそろってから、以下を実行する。

```bash
.venv/bin/python scripts/02_extract_urls.py
.venv/bin/python scripts/03_label_urls.py
.venv/bin/python scripts/04_add_year.py
DATASET_PARSER_CPU=1 .venv/bin/python scripts/07_parse_mmd_context.py
```

ここまでで`data/intermediate/no_kagikakko_extracted_urls.json`、`labelled.csv`、`labelled_with_year.csv`、`pt_cs_ci_dict_output.json`ができる。最後のコマンドはCPU実行の例。原コード同様にGPUを必須にする場合は`DATASET_PARSER_CPU=1`を外す。

参考文献の本文中の引用文を補うには、対応する論文の**full-text TEI XML**を`data/xml/`に配置する必要がある。元のXML生成手順は添付されていない。GROBIDのfull-text APIはその形式のXMLを生成できるため、稼働中のローカルGROBIDサービスがある場合のみ、以下の補助コードを使用できる。この設定が実験当時の方法と同じだとは確認できていない。

```bash
.venv/bin/python scripts/08a_generate_tei_grobid.py
ls data/xml/*.xml
DATASET_PARSER_CPU=1 .venv/bin/python scripts/08_parse_tei_references.py
.venv/bin/python scripts/09_add_reference_info.py
.venv/bin/python scripts/10_combine_context.py
.venv/bin/python scripts/11_split_candidate.py
.venv/bin/python scripts/12_validate_outputs.py
```

`08a`を使わない場合も、元のTEI XMLを`data/xml/`に置けば`08`以降を実行できる。`08`の出力は`xml_ref_dict.json`、`09`は`url_around_info.json`と`reference_merge_report.json`、`10`は`dataset_with_context.csv`と照合レポート、`11`は**新たに作った候補分割**とレポートを生成する。`12`は列・ラベル・分割の整合性を調べ、`data/intermediate/validation_report.json`を出力する。`reference_merge_report.json`の未照合参考文献、`combine_report.json`の未照合URLと`context_status`、`split_report.json`と`validation_report.json`の件数を必ず確認する。17,977件と異なっても、元のデータがない段階では比較結果として表示し、機械的に失敗とは扱わない。

`02b_trim_parentheses_optional.py`は別案で後続に接続されていない。`05_context_diagnostic_incomplete.py`と`06_split_diagnostic_incomplete.py`も通常の実行手順には含めない。

## 8. GitHubへ反映する前に

```bash
git status --short
git add .gitignore README.md REVIEW_JA.md SETUP_JA.md requirements.txt scripts data
git diff --cached --stat
git status --short
```

入力JSON、PDF、`.mmd`、XML、出力データ、`.venv/`、`original/`、`original_additional/`が追加対象に入っていないことを確認してからコミットする。確認が済んだ場合のみ `git commit -m "Add data construction scripts and documentation"` と `git push -u origin HEAD` を実行する。GitHub上にすでにある内容と衝突している場合は、その差分を確認してから統合する。強制pushは行わない。

周辺テキストの生成と候補分割まで実行できるようになったが、元のPWCスナップショット・PDF・TEI XML・実験当時の設定がないため、論文の17,977件やtrain/dev/testの一致は保証できない。詳細はREADMEとREVIEW_JAを参照。
