import csv
import json

# FILE_JSON_PATH = "/mnt/c/users/okada/Desktop/松原研究室B4/研究/PapersWithCodeDatasets_papers20250808/papers-with-abstracts_JST202508081105.json"
# FILE_CSV_PATH = "/mnt/c/users/okada/Desktop/松原研究室B4/研究/2025-0829-making_dataset/train_dev_test_dataset/mydataset_random_2672_papers.csv"
FILE_JSON_PATH = "/workspace/papers-with-abstracts_JST202508081105.json"
FILE_CSV_PATH = "/workspace/2025-0829-making_dataset/train_dev_test_dataset/no_kagikakko_mydataset_random_2672_papers.csv"

def main():
    json_li = reading_json(FILE_JSON_PATH)
    csv_li = reading_csv(FILE_CSV_PATH)
    add_year_list = add_year(json_li,csv_li)
    write_csv("/workspace/2025-0829-making_dataset/train_dev_test_dataset/no_kagikakko_mydataset_random_2672_papers_add_year.csv",add_year_list)

def reading_json(file_path: str):
    """ json ファイルの読み込み"""
    with open(file_path, 'r',encoding='utf-8') as f:
        dataset_li = json.load(f)
    return dataset_li

def reading_csv(file_path: str):
    """ csv ファイルの読み込み"""
    with open(file_path, 'r',encoding='utf-8') as f:
        reader = csv.reader(f)      
        dataset_li = [row for row in reader]
    return dataset_li

def add_year(json_li,csv_li):
    new_csv_li = []
    count = 0
    for i in csv_li:
        for j in json_li:
            if i[3] == j['title']:
                i.append(j['date'])
                if j["date"] == "":
                    count += 1
                new_csv_li.append(i)
                break
    print("add year num:",len(new_csv_li))
    print("no year num:",count)
    return new_csv_li

def write_csv(file_path: str, data: list):
    """ csv ファイルの書き込み"""
    json_keys = ["id", "name", "homepage", "paper_title", "year", "label"] 
    with open(file_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=json_keys,quoting=csv.QUOTE_NONNUMERIC)
        writer.writeheader()
        for item in data:
            row = {
                "id":item[0],
                "name":item[1],
                "homepage":item[2],
                "paper_title": item[3],
                "year":item[5],
                "label":item[4]
            }
            writer.writerow(row)

if __name__ == '__main__':
    main()