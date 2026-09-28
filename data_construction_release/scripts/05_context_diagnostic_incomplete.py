import csv
import json
import re

CSV_FILEPATH = "data/intermediate/labelled_with_year.csv"
JSON_FILEPATH = "data/input/pt_cs_ci_dict_output.json"
WRITE_CSV_PATH = "data/intermediate/context_diagnostic_unused.csv"

def main():
    with open(JSON_FILEPATH,"r",encoding="utf-8") as f:
        json_di = json.load(f)
    with open(CSV_FILEPATH,"r",encoding="utf-8") as fp:
        reader = csv.reader(fp)      
        csv_li = [row for row in reader]

    print("json数：",len(json_di))
    print("csv数：",len(csv_li))
    url_info_li = []
    count = 0
    # 論文タイトル同士マッチ
    for i in csv_li:
        for j in json_di.keys():
            if normalize_title(i[3]) == normalize_title(j):
                i.append(json_di[j])
                url_info_li.append(i)
                break
    # print(url_info_li)
    print(len(url_info_li))
    # URLマッチ



    # write_csv(WRITE_CSV_PATH,)

# --- 正規化関数（特殊記号削除・空白保持・大文字小文字そのまま） ---
def normalize_title(title):
    return re.sub(r'[^A-Za-z0-9\s]', '', title)


# def write_csv(file_path: str, data: list):
#     """ csv ファイルの書き込み"""
#     # json_keys = ["id", "name", "homepage", "paper_title", "year", "label"] 
#     json_keys = ["Id", "Url", "Passage-title", "Citation-sentence", "Citation-info", "Citation-paragraph", "Dataset-name","Year", "Paper-title", "Citation-type", "label"]
#     with open(file_path, 'w', newline='', encoding='utf-8') as f:
#         writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_NONNUMERIC)
#         writer.writeheader()
#         for item in data:
#             # row = {
#             #     "id":item[0],
#             #     "name":item[1],
#             #     "homepage":item[2],
#             #     "paper_title": item[3],
#             #     "year":item[5],
#             #     "label":item[4]
#             # }
#             row = {
#                 "Id":item[0],
#                 "Url":item[2],
#                 "Passage-title":item[],
#                 "Citation-sentence":item[],
#                 "Citation-info":item[],
#                 "Citation-paragraph":item[],
#                 "Dataset-name":item[1],
#                 "Year":item[5],
#                 "Paper-title":item[3],
#                 "Citation-type":item[],
#                 "label":item[4]


#             }
#             writer.writerow(row)

if __name__ == '__main__':
    main()