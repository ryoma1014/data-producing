# 添付コードの照合結果

## 論文の手順とファイル

| 元ファイル | 判断 | 実際の役割 |
| --- | --- | --- |
| `1_making_dataset.py` | 補助的に使用 | PWC datasets JSONを読み、タイトルとhomepageの仮CSVを作る。PDF取得スクリプトはこのファイルの読み込み・タイトル一覧関数をimportするが、仮CSV自体は後続で読まない。 |
| `1_papers_json_pdf_download.py` | PDF取得に使用 | papers JSONから`url_pdf`を取得。`conference_url_pdf`は集計するだけ。ファイル名は論文タイトル由来。 |
| `2_url_extraction_from_mmd.py` | URL抽出に使用 | `.mmd`からURL一覧を抽出。PDF→MMD変換や周辺テキスト抽出はしない。 |
| `2_url_kagikakko_extraction_json.py` | 既定の流れでは不要 | 括弧以前を切り落とした別JSONを作るが、後段の読み込み元はそのJSONではない。 |
| `3_1_making_dataset_produce_or_not_url_classify.py` | ラベル計算に使用 | 単独起動は集計のみ。次のスクリプトから関数としてimportされる。 |
| `3_2_making_dataset_add_neg_ex.py` | CSVの正負ラベル作成に使用 | 分類関数の返すリストから`Produce`/`nonProduce` CSVを作る。 |
| `4_making_dataset_add_year.py` | 日付付加に使用 | CSVの論文タイトルとpapers JSONの`title`が完全一致した行だけに`date`を付ける。 |
| `5_making_dataset_add_around_url_info.py` | 未完成、既定の流れには使えない | `pt_cs_ci_dict_output.json`を読むがURL照合とCSV保存は未実装。 |
| `making_dataset_tdt_divide_year.py` | 未完成、分割の再現には使えない | 年順に並べ、末尾10%をテスト側として選ぶ途中まで。devの分割、CSV保存はコメントアウト。角掛データと重複する論文名を固定リストで除外。 |

## 実行に必要だが添付されなかったもの

1. 実験当時のPWC datasets/papers JSON。元の実験結果と同一の件数を検証するには同じスナップショットが必要。
2. PDFを`.mmd`にする変換ツールと設定。MMDのファイル名のstemと論文タイトルが対応する必要がある。
3. section title、URLを含む文と前後文、脚注・参考文献情報を抽出する処理。`pt_cs_ci_dict_output.json`の生成方法も不明。
4. `random`を含む旧CSV名が示唆するシャッフル処理、実際のtrain/dev/test作成処理、報告済み分割の一覧。提示コードにはない。

## 注意して照合すべき実装上の点

- READMEに記した多対多比較により、同じ抽出URLの重複や正負への重複登録が起こり得る。`3_2`では各正例の名前を最初に一致したdatasetから選ぶ。
- `2_url_extraction_from_mmd.py`はURLを紙面の出現単位で保持せず、論文ごとに重複排除する。本文・脚注・参考文献の位置も出力しない。論文の入力形式と異なる可能性がある。
- `1_papers_json_pdf_download.py`はタイトルの部分一致が複数あるとダウンロードせず、`url_pdf`が空でも`conference_url_pdf`へ切り替えない。PDF取得先の状況によって件数は変わる。
- `4_making_dataset_add_year.py`はCSVヘッダを入力データとして読むが、papers JSON中のtitleと一致しなければ自然に除外される。`year`の値は年だけではなく日付文字列。
- `making_dataset_tdt_divide_year.py`のハードコードされた除外リストとテスト選択規則から、論文記載の8:1:1分割をそのまま作れたとは確認できない。

## 公開前に行う確認

元の中間成果物があれば、各段階のJSON/CSVと本パッケージの結果を行単位で比較する。特に抽出URLとラベルの重複、正負の件数を比較する。その後、欠けたMMD変換・周辺文抽出・分割の元コードを追加し、最終の17,977件、正例3,185件と分割13,715/1,635/2,627件を照合する。異なる場合は、論文とコードのどちらの記述を訂正すべきか共著者と確認する。

元コードは`original/`に保持している。`scripts/`には実行場所の調整のみを行った。元のCSVや実験データを所持していないため、論文の件数との一致を保証するものではない。
