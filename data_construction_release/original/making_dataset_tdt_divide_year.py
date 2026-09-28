import csv
from sklearn.model_selection import train_test_split
import random
from datetime import datetime
from collections import defaultdict

def main():
    # file_path = "/mnt/ssd/研究/2025-0829-making_dataset/train_dev_test_dataset/mydataset.csv"
    file_path = "/workspace/2025-0829-making_dataset/mydatasets/no_kagikakko_mydataset_random_2672_papers_add_year.csv"
    dataset_li = reading_mydataset_csv(file_path)
    random.seed(42)
    train_dev_li = train_dev_test_divide_paper_years(dataset_li)
    
    sampled_li = balanced_random_sample(train_dev_li, sample_size=100)
    print_samples_by_year(sampled_li)

def balanced_random_sample(data, sample_size=100):
    """
    年代（西暦年）ごとにできるだけ均等にサンプリングする関数

    Args:
        data (list[dict]): [{"title": ..., "date": "yyyy-mm-dd"}, ...]
        sample_size (int): 取り出す要素数

    Returns:
        list[dict]: サンプリングされたリスト
    """
    # 年ごとにデータをまとめる
    year_groups = defaultdict(list)
    for item in data:
        date = item.get("date")
        if not date:
            continue
        year = date[:4]  # "yyyy-mm-dd" → "yyyy"
        year_groups[year].append(item)
    
    # 各年のリストを取得
    years = list(year_groups.keys())
    n_years = len(years)
    if n_years == 0:
        return []
    
    # 各年から取る件数を均等に割り当て
    per_year = sample_size // n_years
    remainder = sample_size % n_years

    sampled = []
    for year in years:
        group = year_groups[year]
        k = min(per_year, len(group))
        sampled.extend(random.sample(group, k))

    # 余りの分をランダムに補充（全データから）
    remaining_needed = sample_size - len(sampled)
    if remaining_needed > 0:
        all_remaining = [
            x for year, items in year_groups.items() for x in items if x not in sampled
        ]
        if len(all_remaining) > remaining_needed:
            sampled.extend(random.sample(all_remaining, remaining_needed))
        else:
            sampled.extend(all_remaining)
    
    # シャッフルして最終リストを返す
    random.shuffle(sampled)
    return sampled[:sample_size]

from collections import defaultdict

def print_samples_by_year(sampled_data):
    """
    年代ごとにサンプリング結果を標準出力する関数

    Args:
        sampled_data (list[dict]): [{"title": ..., "date": "yyyy-mm-dd"}, ...]
    """
    # 年代ごとに分類
    year_groups = defaultdict(list)
    for item in sampled_data:
        date = item.get("date")
        if not date:
            continue
        year = date[:4]
        year_groups[year].append(item)
    
    # 年代順にソートして出力
    for year in sorted(year_groups.keys()):
        group = year_groups[year]
        print(f"\n=== {year}年 ({len(group)}件) ===")
        for i, item in enumerate(group, 1):
            print(f"{i:02d}. {item['title']} ({item['date']})")


def reading_mydataset_csv(file_path: str):
    """ json ファイルの読み込み"""
    with open(file_path, 'r',encoding='utf-8') as f:
        reader = csv.reader(f)      
        dataset_li = [row for row in reader]
    return dataset_li

def train_dev_test_divide_paper_years(dataset_li:list):
    """データセットを学習用、開発用、テスト用に分割"""
    train_li = []
    dev_li = []
    test_li = []
    tsunokake_dup_list = ['WikiCREM: A Large Unsupervised Corpus for Coreference Resolution', 'INFOTABS: Inference on Tables as Semi-structured Data', 'Visual Story Post-Editing', 'MultiWOZ -- A Large-Scale Multi-Domain Wizard-of-Oz Dataset for Task-Oriented Dialogue Modelling', 'Conversational Document Prediction to Assist Customer Care Agents', 'Investigating representations of verb bias in neural language models', 'Explainable Automated Fact-Checking for Public Health Claims', 'A Dataset for Document Grounded Conversations', 'HERO: Hierarchical Encoder for Video+Language Omni-representation Pre-training', 'WiC: the Word-in-Context Dataset for Evaluating Context-Sensitive Meaning Representations', 'MathQA: Towards Interpretable Math Word Problem Solving with Operation-Based Formalisms', 'An annotated dataset of literary entities', 'Digital Voicing of Silent Speech', 'IIRC: A Dataset of Incomplete Information Reading Comprehension Questions', 'What You See is What You Get: Visual Pronoun Coreference Resolution in Dialogues', 'MLQA: Evaluating Cross-lingual Extractive Question Answering', 'Are Missing Links Predictable? An Inferential Benchmark for Knowledge Graph Completion', 'HellaSwag: Can a Machine Really Finish Your Sentence?', 'CodRED: A Cross-Document Relation Extraction Dataset for Acquiring Knowledge in the Wild', 'TalkSumm: A Dataset and Scalable Annotation Method for Scientific Paper Summarization Based on Conference Talks']
    papers_li = []
    papers_title_set = set()

    for i in dataset_li[1:]:
        id = i[0]
        name = i[1]
        url= i[2]
        title = i[3]
        date = i[4]
        label = i[5]

        if title not in papers_title_set:
            papers_title_set.add(title)
            papers_li.append({"title": title, "date": date})

    # ソート処理（昇順）
    papers_li_sorted = sorted(
        papers_li,
        key=lambda x: datetime.strptime(x["date"], "%Y-%m-%d")
    )
    
    # paper_titles = []
    # for p in papers_li_sorted:
        # print(p["date"], p["title"])
    # print("論文数（２６７２想定）：",len(papers_li_sorted))

    # テストデータ作成
    train_title_date_li,test_title_date_li = train_test_split(
        papers_li_sorted,
        shuffle=False, 
        random_state=111, 
        test_size=0.1
        )

    test_li:list[dict] = []
    for j in test_title_date_li:
        for i in dataset_li[1:]:
            id = i[0]
            name = i[1]
            url= i[2]
            title = i[3]
            date = i[4]
            label = i[5]
            
            if title == j["title"]:
                test_li.append({"id":id,"name":name,"url":url,"title":title,"date":date,"label":label})
    # 角掛けデータと重複しているものを一旦除外
    for i in train_title_date_li:
        if i["title"] in tsunokake_dup_list:
            train_title_date_li.remove(i)
    print(len(train_title_date_li))
    return train_title_date_li

#     # いじるとしたらここから、テストデータは触らない
#     train_title_date_li,dev_title_date_li = train_test_split(
#         train_title_date_li,
#         shuffle=True, 
#         random_state=12539, 
#         test_size=1/9
#     )
#     train_li:list[dict] = []
#     dev_li:list[dict] = []
#     for j in train_title_date_li:
#         for i in dataset_li[1:]:
#             id = i[0]
#             name = i[1]
#             url= i[2]
#             title = i[3]
#             date = i[4]
#             label = i[5]
            
#             if title == j["title"]:
#                 train_li.append({"id":id,"name":name,"url":url,"title":title,"date":date,"label":label})

#     for j in dev_title_date_li:
#         for i in dataset_li[1:]:
#             id = i[0]
#             name = i[1]
#             url= i[2]
#             title = i[3]
#             date = i[4]
#             label = i[5]
            
#             if title == j["title"]:
#                 dev_li.append({"id":id,"name":name,"url":url,"title":title,"date":date,"label":label})
#     # return train_li,dev_li,test_li
#     random.seed(42)
#     train_li = random.sample(train_li,len(train_li))
#     dev_li = random.sample(dev_li,len(dev_li))
#     test_li = random.sample(test_li,len(test_li))
#     # 書き込み
#     json_keys = ["id", "name", "homepage", "paper_title", "date","label"]             # json ファイルから欲しい key を取得・ココナに取得すればいいかわからん
#     with open("/workspace/2025-0829-making_dataset/mydatasets/train_mydataset_random_2672_papers_add_year.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_ALL)
#         writer.writeheader()
#         for item in train_li:
#             row = {
#                 "id":item["id"],
#                 "name":item["name"],
#                 "homepage":item["url"],
#                 "paper_title": item["title"],
#                 "date":item["date"],
#                 "label":item["label"]
#             }
#             writer.writerow(row)
    
#     with open("/workspace/2025-0829-making_dataset/mydatasets/dev_mydataset_random_2672_papers_add_year.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_ALL)
#         writer.writeheader()
#         for item in dev_li:
#             row = {
#                 "id":item["id"],
#                 "name":item["name"],
#                 "homepage":item["url"],
#                 "paper_title": item["title"],
#                 "date":item["date"],
#                 "label":item["label"]
#             }
#             writer.writerow(row)

#     with open("/workspace/2025-0829-making_dataset/mydatasets/test_mydataset_random_2672_papers_add_year.csv", "w", newline="", encoding="utf-8") as f:
#         writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_ALL)
#         writer.writeheader()
#         for item in test_li:
#             row = {
#                 "id":item["id"],
#                 "name":item["name"],
#                 "homepage":item["url"],
#                 "paper_title": item["title"],
#                 "date":item["date"],
#                 "label":item["label"]
#             }
#             writer.writerow(row)


if __name__ == '__main__':
    main()

