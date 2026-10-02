import json 
import csv

with open("/workspace/2025-0829-making_dataset/parser/url_around_info.json", "r" , encoding="utf-8") as f:
    url_around_info_di = json.load(f)
with open("/workspace/2025-0829-making_dataset/mydatasets/no_kagikakko_mydataset_random_2672_papers_add_year.csv","r",encoding="utf-8") as fp:
    reader = csv.reader(fp)      
    dataset_li = [row for row in reader]

header = dataset_li[0]
new_columns = ["Passage-title","Citation-sentence","Citation-info", "Citation-paragraph","Citation-type"]
header.append(new_columns)
new_dataset = [header]

# 論文タイトルとURLで結びつける
for k_title,v_li in url_around_info_di.items():
    for i in dataset_li[1:]:
        if i[3] == k_title:
            for j_di in v_li:
                if i[2] in j_di["URL"]:
                    new_row = i + [
                        j_di.get("Passage-title", ""),  # JSON内のキー名に応じて変更
                        j_di.get("Citation-sentence", ""),
                        j_di.get("Citation-info", ""),
                        j_di.get("Citation-paragraph", ""),
                        j_di.get("Citation-type", "")
                    ]
                    new_dataset.append(new_row)

output_path = "/workspace/2025-0829-making_dataset/parser/mydatasets_with_url_info.csv"

with open(output_path, "w", encoding="utf-8", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(new_dataset)

print(f"✅ 保存完了: {output_path}")