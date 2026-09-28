import making_dataset_produce_or_not_url_classify
import pandas as pd
import csv
import json

def main():
    dataset_li = making_dataset_produce_or_not_url_classify.reading_dataset_json()
    extracted_url_di = making_dataset_produce_or_not_url_classify.reading_extracted_urls_json()
    print("extracted_urls.json の数:", len(extracted_url_di.keys()))
    papers_title_list = making_dataset_produce_or_not_url_classify.paper_verified_paper_nodup(dataset_li)
    print("正規化後タイトル数:", len(papers_title_list))
    title_url_dict = making_dataset_produce_or_not_url_classify.making_title_url_dict(dataset_li, papers_title_list)
    # non_produce_url_dict= making_dataset_produce_or_not_url_classify.check_produce_url(extracted_url_di, title_url_dict)
    # 正例追加用
    produce_url_dict,non_produce_url_dict= making_dataset_produce_or_not_url_classify.check_produce_url(extracted_url_di, title_url_dict)

    # id取得
    DATASET_PATH = "data/intermediate/labelled.csv"

    with open("data/input/datasets_JST202508081105.json") as f:
    # with open("/mnt/ssd/研究/PapersWithCodeDatasets_dataset20250808/datasets_JST202508081105.json") as f:
    # with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/PapersWithCodeDatasets_papers20250808/datasets_JST202508081105.json") as f:
        datasetjson_li: list[dict] = json.load(f)
    # データセットに正例追加
    json_keys = ["id", "name", "homepage", "paper_title", "label"]             # json ファイルから欲しい key を取得・ココナに取得すればいいかわからん
    with open(DATASET_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_ALL)
        writer.writeheader()
        id = 0
        for k_title,v_urls in produce_url_dict.items():
            for data_i in datasetjson_li:
                title = None
                if data_i["paper"] and not data_i["verified_paper"]:
                    title = data_i["paper"]["title"]
                elif not data_i["paper"] and data_i["verified_paper"]:
                    title = data_i["verified_paper"]["title"]
                elif data_i["paper"] and data_i["verified_paper"]:
                    title = data_i["paper"]["title"]
                else:
                    continue
                if k_title == title:

                    for v_url in v_urls:
                        row = {
                            "id":id,
                            "name":data_i["name"],
                            "homepage":v_url,
                            "paper_title": k_title,
                            "label":"Produce"
                        }
                        # 論文タイトルもしくはURLがない場合はデータセットに含まない
                        if row["homepage"] == "" or row["paper_title"] == "":
                            continue 
                        id += 1
                        writer.writerow(row)
                    break
    df = pd.read_csv(DATASET_PATH)
    row, col = df.shape
    # データセットに負例追加
    with open(DATASET_PATH, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_ALL)
        id = row
        for k_title,v_urls in non_produce_url_dict.items():
            for v_url in v_urls:
                row = {
                    "id":id,
                    "name":" ",
                    "homepage":v_url,
                    "paper_title": k_title,
                    "label":"nonProduce"
                }
                # 論文タイトルもしくはURLがない場合はデータセットに含まない
                if row["homepage"] == "" or row["paper_title"] == "":
                    continue 
                id += 1
                writer.writerow(row)

if __name__ == '__main__':
    main()
