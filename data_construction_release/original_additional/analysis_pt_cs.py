import json
import copy

def reading_json(file_path):
    with open(file_path, "r" , encoding="utf-8") as f:
        dataset_di = json.load(f)
    return dataset_di

pt_cs_ci_dict = reading_json("/workspace/2025-0829-making_dataset/parser/pt_cs_ci_dict_output.json")
no_sentence_not_reference_count =0 
all_count = 0
no_url_count = 0
for k,v in pt_cs_ci_dict.items():
    for i in v:
        all_count += 1
        if i["Citation-sentence"] == "" and i["Citation-type"] != "Reference":
            no_sentence_not_reference_count += 1
        if i["URL"] == "":
            no_url_count += 1
print("すべての要素の数：",all_count)
print("Reference以外でCitation-sentenceが登録されていないものの数：",no_sentence_not_reference_count)
print("URLが登録されていないモノの数：",no_url_count)