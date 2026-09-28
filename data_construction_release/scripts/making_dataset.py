import json
import csv

def main():
    dataset_li = reading_json()
    # check_key(dataset_li)
    # paper_title_nodup(dataset_li)
    # paper_verified_paper_nodup(dataset_li)
    # paper_dup_count(dataset_li)
    making_csv_title_url(dataset_li)
    # making_csv_all(dataset_li)
    count_title_url_papers(dataset_li)
    count_title_url_papers_debug(dataset_li)

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
    # with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/PapersWithCodeDatasets_papers20250808/datasets_JST202508081105.json") as f:
    # with open("/mnt/ssd/研究/PapersWithCodeDatasets_dataset20250808/datasets_JST202508081105.json") as f:
    with open("data/input/datasets_JST202508081105.json") as f:
        dataset_li:list[dict] = json.load(f)
    return dataset_li

def check_key(dataset:list):
    """key の確認"""
    key_li:list[str] = []
    for i_di in dataset:
        for k,v in i_di.items():
            # print(k)
            if k in key_li:
                continue
            else:
                key_li.append(k)
    print(len(key_li))
    print(key_li)

def paper_title_nodup(dataset:list):
    papers_title_list:list = []
    for i_di in dataset:
        """ 論文タイトルが記述されてない場合は取得しない"""
        if i_di["paper"] is None:
            continue
        else:
            """論文タイトルをリスト化、重複は削除"""
            if i_di["paper"]["title"] in papers_title_list:
                continue
            else:
                papers_title_list.append(i_di["paper"]["title"])
    print(papers_title_list)
    print(len(papers_title_list))

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
    # print(a,b,c,d)
    # print(papers_title_list)
    # print(len(papers_title_list))
    return papers_title_list

def paper_dup_count(dataset:list):
    """論文の重複カウント用"""
    papers_title_list:list = []
    papers_title_count_dict:dict = {}
    for i_di in dataset:
        """ 論文タイトルが記述されてない場合は取得しない"""
        if i_di["paper"] is None:
            continue
        else:
            """論文タイトルをリスト化、重複は削除"""
            if i_di["paper"]["title"] in papers_title_list:
                papers_title_count_dict[i_di["paper"]["title"]] += 1
            else:
                papers_title_count_dict[i_di["paper"]["title"]] = 1
                papers_title_list.append(i_di["paper"]["title"])

    papers_title_count_dict = sorted(papers_title_count_dict.items(), key=lambda x:x[1])
    # print(papers_title_count_dict)
    # print(papers_title_list)
    # print(len(papers_title_list))

    """論文検索"""
    # basis_paper = semantic_scholar_api.find_basis_paper(papers_title_list)
    # semantic_scholar_api.find_recommendations(basis_paper)

"""Produce の csv ファイル作成（論文タイトルとURLが両方ある場合のみデータセットに含む）"""
def making_csv_title_url(dataset:list):
    json_keys = ["id", "name", "homepage", "paper_title", "label"]             # json ファイルから欲しい key を取得・ココナに取得すればいいかわからん
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
    
    # lines = []
    # with open("mydataset.csv","r",encoding="utf-8") as f:
    #     for i, line in enumerate(f):
    #         if i == 0:
    #             lines.append(line)
    #         else:
    #             parts = line.strip().split(",")
    #             # parts[1] = f'"{parts[1]}"'
    #             parts[2] = f'"{parts[2]}"'
    #             # parts[3] = f'["{parts[3]}]'
    #             # parts[4] = f'"{parts[4]}"'
    #             lines.append(",".join(parts)+"\n")
    # with open("mydataset.csv", "w",encoding="utf-8") as f:
    #     f.writelines(lines)

def making_csv_all(dataset:list):
    """Produce の csv ファイル作成（全部追加）"""
    json_keys = ["id","name", "homepage", "paper_title", "label"]             # json ファイルから欲しい key を取得・ココナに取得すればいいかわからん
    with open("dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=json_keys)
        writer.writeheader()
        id = 0
        for item in dataset:
            row = {
                "id":id,
                "name":item.get("name", ""),
                "homepage":item.get("homepage",""),
                "paper_title": f"[{get_verified_paper_title(item)}]",
                "label":"Produce"
            }
            id += 1
            writer.writerow(row)

def count_title_url_papers(dataset:list):
    """Papers With Code Dataset に論文タイトルとURLが両方登録されている論文のカウント用（paper or verified_paper）"""
    count_list = []
    id = 0
    for item in dataset:
        row = {
            "id":id,
            "homepage":item.get("homepage",""),
            "verified_paper_title": get_verified_paper_title(item),
            "label":"Produce"
        }
        # 論文タイトルもしくはURLがない場合はデータセットに含まない
        if row["homepage"] == "" or row["verified_paper_title"] == "":
            continue 
        elif row["verified_paper_title"] in count_list:
            continue
        elif row["verified_paper_title"] not in count_list:
            count_list.append(row["verified_paper_title"])
        id += 1

    print(len(count_list))

def count_title_url_papers_debug(dataset: list):
    counted_titles = set()
    skipped_no_url = 0
    skipped_no_title = 0

    for item in dataset:
        homepage = item.get("homepage")
        title = get_verified_paper_title(item)

        if not homepage:
            skipped_no_url += 1
            continue
        if not title:
            skipped_no_title += 1
            continue

        counted_titles.add(title)

    print("ユニークタイトル数:", len(counted_titles))
    print("URLなしでスキップされた数:", skipped_no_url)
    print("タイトルなしでスキップされた数:", skipped_no_title)


if __name__ == '__main__':
    main()