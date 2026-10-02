import json

with open("/workspace/2025-0829-making_dataset/parser/url_around_info.json", "r" , encoding="utf-8") as f:
    dataset_di = json.load(f)
ref_count = 0
no_combine_ref_count = 0

for i in dataset_di.values():
    for j in i:
        if j["Citation-type"] == "Reference":
            ref_count += 1
            # break     # 論文カウント用
        if j["Citation-info"] == "" and j["Citation-type"] == "Reference":
            no_combine_ref_count += 1 



print("URLを含むReferenceの数",ref_count)
print("refと本文が結びついていない物の数",no_combine_ref_count)