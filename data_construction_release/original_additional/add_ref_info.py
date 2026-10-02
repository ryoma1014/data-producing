import json
import copy
from rapidfuzz import fuzz  # ← ここがポイント

def reading_json(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        dataset_di = json.load(f)
    return dataset_di

# === 入力データ ===
xml_ref_di = reading_json("/workspace/2025-0829-making_dataset/parser/xml_ref_dict.json")
mmd_di = reading_json("/workspace/2025-0829-making_dataset/parser/pt_cs_ci_dict_output.json")

url_match_count = 0
no_sentence_count = 0
count = 0

# 類似度の閾値（0〜100）
threshold = 89  # difflibの0.89に対応

# 類似度関数（rapidfuzzは0〜100のスコアを返す）
def similar(a, b):
    return fuzz.ratio(a, b)

# === メイン処理 ===
for mmd_pt, mmd_li in mmd_di.items():
    for xml_pt, xml_li in xml_ref_di.items():
        if xml_pt == mmd_pt:
            # new_li = mmd_li
            for mmd_paper_di in mmd_li:
                hit_count = 0

                for xml_paper_di in xml_li:
                    # sim = similar(xml_paper_di["Citation-info"], mmd_paper_di["URL"])

                    # URL類似度で判定（rapidfuzzは0〜100）
                    # if sim >= threshold and mmd_paper_di["Citation-type"] == "Reference":
                    if xml_paper_di["Citation-info"]==mmd_paper_di["URL"] and mmd_paper_di["Citation-type"] == "Reference":
                        url_match_count += 1
                        hit_count += 1

                        if hit_count == 1:
                            # 1回目のヒット → 上書き
                            mmd_paper_di["Citation-paragraph"] = xml_paper_di["Citation-paragraph"]
                            mmd_paper_di["Citation-sentence"] = xml_paper_di["Citation-sentence"]
                            mmd_paper_di["Passage-title"] = xml_paper_di["Paragraph-title"]
                            mmd_paper_di["Citation-type"] = xml_paper_di["Citation-type"]

                            # Citation-sentenceが空ならカウント
                            if not xml_paper_di["Citation-sentence"]:
                                no_sentence_count += 1

                            count += 1
                        else:
                            # 2回目以降 → 新規作成
                            new_di = {
                                "Passage-title": xml_paper_di["Paragraph-title"],
                                "Citation-paragraph": xml_paper_di["Citation-paragraph"],
                                "Citation-sentence": xml_paper_di["Citation-sentence"],
                                "Citation-info": xml_paper_di["Citation-info"],
                                "Citation-type": xml_paper_di["Citation-type"],
                                "URL": xml_paper_di["Citation-info"],
                            }
                            mmd_li.append(new_di)

            # mmd_di[mmd_pt] = new_li

# === 結果出力 ===
print("ReferenceURLが一回目にヒットした数：", count)
print("urlがマッチした回数：", url_match_count)
print("urlがマッチしたもののうち、Citation-sentenceが登録されていないものの数：", no_sentence_count)

output_path = "/workspace/2025-0829-making_dataset/parser/url_around_info.json"
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(mmd_di, f, ensure_ascii=False, indent=2)
print(f"保存しました: {output_path}")
