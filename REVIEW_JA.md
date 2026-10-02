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
2. PDF→`.mmd`変換ツールはNougatと判明。実験当時のバージョン、モデル、オプション、失敗時の再処理方法は未確認。MMDのファイル名のstemと論文タイトルが対応する必要がある。
3. 参考文献の本文中の引用を抽出するためのTEI XML生成コマンドと設定。追加コードでMMDから`pt_cs_ci_dict_output.json`を生成する方法は判明したが、前後文を連結する元コードは未提供。
4. `random`を含む旧CSV名が示唆するシャッフル処理、実際のtrain/dev/test作成処理、報告済み分割の一覧。提示コードにはない。

## 追加8ファイルの照合結果

| 元ファイル | 実際の役割 | 判断 |
| --- | --- | --- |
| `parser_footnote.py` | MMDを節・段落・文に分け、本文URLと脚注・参考文献URLを`pt_cs_ci_dict_output.json`へ記録 | 後期版として`07_parse_mmd_context.py`へ接続。GPU必須だった箇所にCPU実行の明示的な切替を追加し、脚注タグ生成時の未初期化変数を修正。 |
| `parser_footnote_copy.py` | 同種の処理の旧版。URLを`<<url>>`などで包むなど出力形式が異なる | 既定の流れには使わず、`original_additional/`に保存。後期版と混用しない。 |
| `parser_reference.py` | TEI XMLの`biblStruct`内URLと本文の`ref type="bibr"`を照合し、引用の節・段落・文をJSON化 | `08_parse_tei_references.py`へ接続。元出力名`xml_ref_dict_not_locatebase.json`と次段の期待する`xml_ref_dict.json`の食い違いを接続。 |
| `add_ref_info.py` | MMD側の参考文献レコードへTEI側の引用文を付ける意図 | 元コードは書誌情報文字列とURLを比較しており一致しにくい。同じリストへ反復中に追加する危険もある。`09_add_reference_info.py`で`URL`対`URL`比較に直し、追加分は反復後に挿入。元コードは保存。 |
| `combine_csv_url_info.py` | 日付・ラベル付きCSVとURL周辺情報JSONを論文タイトル・URLで結合 | 元コードの`header.append(new_columns)`は5列を1列として追加する。URL部分文字列照合も誤一致の可能性がある。`10_combine_context.py`で列を分け、URLはラベル判定と同じ正規化照合を既定にした。元方式はオプションで指定可。 |
| `analysis_pt_cs.py` | 文・URLの欠損を数える | 集計専用。 |
| `pt_cs_ci_dict_analy.py` | URLのない脚注レコードを数える | 集計専用。 |
| `url_around_info_analysis.py` | 本文の引用文と結び付かない参考文献の件数を数える | 集計専用。 |

追加されたコードで、これまで不明だった`pt_cs_ci_dict_output.json`の生成元が分かった。参考文献経路はPDF→TEI XMLが別途必要。XMLの要素構造はGROBIDのfull-text TEIに合うが、**実際に用いたXML生成ソフト・バージョン・オプションは確認できない**。`08a_generate_tei_grobid.py`はGROBIDサービスを利用するために新設した補助コードで、歴史的事実を表すものではない。

論文に記載された「URLを含む文と同一段落内の前後文」について、元のMMDパーサが保存するのはURLを含む一文と段落全文まで。前後文を選択する元コードは含まれていない。`10_combine_context.py`で同じspaCyモデルを用いて段落から前後文を取る処理を新設し、照合不能をレポートに残す。元の実験の文境界・例数と一致したかは別途照合が必要。

`11_split_candidate.py`は論文の年順8:1:1に基づく**候補**を出力するが、元コードでコメントアウトされていたdevのランダム抽出、角掛データ重複除外、元の紙面のtrain/dev/testメンバーシップを復元したものではない。件数レポートが一致しても、行の一致を確認する必要がある。

## 注意して照合すべき実装上の点

- READMEに記した多対多比較により、同じ抽出URLの重複や正負への重複登録が起こり得る。`3_2`では各正例の名前を最初に一致したdatasetから選ぶ。
- `2_url_extraction_from_mmd.py`はURLを紙面の出現単位で保持せず、論文ごとに重複排除する。本文・脚注・参考文献の位置も出力しない。論文の入力形式と異なる可能性がある。
- `1_papers_json_pdf_download.py`はタイトルの部分一致が複数あるとダウンロードせず、`url_pdf`が空でも`conference_url_pdf`へ切り替えない。PDF取得先の状況によって件数は変わる。
- `4_making_dataset_add_year.py`はCSVヘッダを入力データとして読むが、papers JSON中のtitleと一致しなければ自然に除外される。`year`の値は年だけではなく日付文字列。
- `making_dataset_tdt_divide_year.py`のハードコードされた除外リストとテスト選択規則から、論文記載の8:1:1分割をそのまま作れたとは確認できない。

## 公開前に行う確認

元の中間成果物があれば、各段階のJSON/CSVと本パッケージの結果を行単位で比較する。特にNougatの出力、抽出URLとラベルの重複、正負の件数を比較する。その後、欠けた周辺文抽出・分割の元コードを追加し、最終の17,977件、正例3,185件と分割13,715/1,635/2,627件を照合する。異なる場合は、論文とコードのどちらの記述を訂正すべきか共著者と確認する。

`12_validate_outputs.py`でCSV列、ラベル、分割の行・論文単位の整合性を検査できる。`validation_report.json`の論文件数との差、`combine_report.json`の未照合行、文脈未特定行を見直すこと。構造検査の合格は、元実験との同一性を証明しない。

元コードは`original/`と`original_additional/`に保持している。`scripts/01`～`06`は主に実行場所の調整、`07`以降には明示した修正・再構成が含まれる。元のCSVや実験データを所持していないため、論文の件数との一致を保証するものではない。
