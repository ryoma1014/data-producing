import json
import csv

def main():
    dataset_li = reading_json()
    making_csv_title_url(dataset_li)

def get_verified_paper_title(item: dict) -> str:
    """
    JSON要素から paper.title, verified_paper.title を取り出す
    どちらも None または存在しない場合は "" を返す
    """
    p = item.get("paper")
    vp = item.get("verified_paper")
    if isinstance(p,dict):
        return p.get("title", "")
    elif isinstance(vp, dict):
        return vp.get("title","")
    return ""   # verified_paper が None や他の型なら空文字

def reading_json():
    """ json ファイルの読み込み"""
    with open("data/input/datasets_JST202508081105.json") as f:
        dataset_li:list[dict] = json.load(f)
    return dataset_li

def paper_verified_paper_nodup(dataset:list):
    """paperとverified_paper を考える、datasetに登録されている論文タイトルの重複なしリストを作る"""
    papers_title_list:list = []
    a = 0
    b = 0
    c = 0
    d = 0
    for i_di in dataset:
        """ 論文タイトルが記述されてない場合は取得しない"""
        if i_di["paper"] is not None and i_di["verified_paper"] is None:
            a += 1
            if i_di["paper"]["title"] in papers_title_list:
                continue
            else:
                papers_title_list.append(i_di["paper"]["title"])
        elif i_di["paper"] is None and i_di["verified_paper"] is not None:
            b += 1
            if i_di["verified_paper"]["title"] in papers_title_list:
                continue
            else:
                papers_title_list.append(i_di["verified_paper"]["title"])
        elif i_di["paper"] is None and i_di["verified_paper"] is None:
            c += 1
            continue
        else:
            d += 1
            """論文タイトルをリスト化、重複は削除"""
            if i_di["paper"]["title"] in papers_title_list:
                continue
            else:
                papers_title_list.append(i_di["paper"]["title"])

    return papers_title_list

"""Produce の csv ファイル作成（論文タイトルとURLが両方ある場合のみデータセットに含む）"""
def making_csv_title_url(dataset:list):
    json_keys = ["id", "name", "homepage", "paper_title", "label"]
    with open("data/intermediate/pwc_pairs.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_keys, quoting=csv.QUOTE_ALL)
        writer.writeheader()
        id = 0
        for item in dataset:
            row = {
                "id":id,
                "name":item.get("name", ""),
                "homepage":item.get("homepage",""),
                "paper_title": get_verified_paper_title(item),
                "label":"Produce"
            }
            # 論文タイトルもしくはURLがない場合はデータセットに含まない
            if row["homepage"] == "" or row["paper_title"] == "":
                continue 
            id += 1
            writer.writerow(row)

if __name__ == '__main__':
    main()