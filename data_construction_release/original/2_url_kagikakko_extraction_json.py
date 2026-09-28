import json

def main():
    dataset_di = reading_dataseturl_json()
    for v_li in dataset_di.values():
        for i, url in enumerate(v_li):
            # "(" と ")" の位置を調べる
            k1_index = url.find("(")
            k2_index = url.find(")")

            # 両方とも見つからない場合 → 何もしない
            if k1_index == -1 and k2_index == -1:
                continue

            # 見つかった方のうち、位置が小さい方を使う
            indices = [idx for idx in [k1_index, k2_index] if idx != -1]
            cut_index = min(indices)

            v_li[i] = url[:cut_index]



    writing_dataset_json(dataset_di)

def reading_dataseturl_json():
    with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/2025-0829-making_dataset/new_next_extracted_urls.json") as f:
        dataset_di = json.load(f)
    return dataset_di

def writing_dataset_json(dataset_di):
    with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/2025-0829-making_dataset/perfect_extracted_urls.json", "w") as f:
        json.dump(dataset_di, f, indent=4, ensure_ascii=False)
    return

if __name__ == "__main__":
    main()