import json

# with open("/workspace/2025-0829-making_dataset/parser/pt_cs_ci_dict_output.json", "r" , encoding="utf-8") as f:
with open("/mnt/c/Users/okada/Desktop/松原研究室B4/研究/parser_copy/pt_cs_ci_dict_output.json", "r" , encoding="utf-8") as f: 
    dataset_di = json.load(f)
ref_count = 0
for i in dataset_di.values():
    for j in i:
        if j["Citation-type"] == "Footnote" and j["URL"] == "":
            ref_count += 1
            # break     # 論文カウント用

print(ref_count)