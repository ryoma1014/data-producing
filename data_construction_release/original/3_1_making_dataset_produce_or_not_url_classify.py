import json
import re

def normalize_title(title: str) -> str:
    """タイトルを英数字のみに正規化（空白・記号削除、小文字化）"""
    if not title:
        return ""
    normalized = re.sub(r'[^A-Za-z0-9]', '', title)  # 英数字以外削除
    return normalized.lower().strip()  # 大文字小文字を無視 & 両端空白削除

def main():
    dataset_li = reading_dataset_json()
    extracted_url_di = reading_extracted_urls_json()
    print("extracted_urls.json の数:", len(extracted_url_di.keys()))
    papers_title_list = paper_verified_paper_nodup(dataset_li)
    print("正規化後タイトル数:", len(papers_title_list))
    title_url_dict = making_title_url_dict(dataset_li, papers_title_list)

    nozero_title_url_dict = {}
    for k, v in title_url_dict.items():
        if v:  # 空リストはスキップ
            nozero_title_url_dict[k] = v

    produce_or_non_dict = check_produce_url(extracted_url_di, nozero_title_url_dict)
    print("produce_url paper number:", len(produce_or_non_dict[0]))
    print("non_produce_url paper number:", len(produce_or_non_dict[1]))
    print("nozero_title_url_dict:", len(nozero_title_url_dict))
    print("データセットURLが登録されていない数：", len(title_url_dict) - len(nozero_title_url_dict))

def reading_dataset_json():
    """ json ファイルの読み込み"""
    with open("/workspace/datasets_JST202508081105.json") as f:
    # with open("/mnt/ssd/研究/PapersWithCodeDatasets_dataset20250808/datasets_JST202508081105.json") as f:
    # with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/PapersWithCodeDatasets_papers20250808/datasets_JST202508081105.json") as f:
        dataset_li: list[dict] = json.load(f)
    return dataset_li

def reading_extracted_urls_json():
    """ json ファイルの読み込み"""
    with open("/workspace/2025-0829-making_dataset/no_kagikakko_extracted_urls.json") as f:
    # with open("/workspace/2025-0829-making_dataset/extracted_urls.json") as f:
    # with open("/mnt/ssd/研究/2025-0829-making_dataset/extracted_urls.json") as f:
    # with open("/mnt/c/users/okada/Desktop/松原研究室B4/研究/2025-0829-making_dataset/new_next_extracted_urls.json") as f:
        dataset_li: dict = json.load(f)
    return dataset_li

# dict{title:url}
def paper_verified_paper_nodup(dataset: list):
    """paper と verified_paper を考慮し、重複を除いたタイトルリストを返す"""
    papers_title_list: list = []
    papers_title_norm_list = []
    seen_titles = []  # 生タイトル
    norm_seen = []    # 正規化後タイトル

    for i_di in dataset:
        # 論文タイトルを取得（どちらか存在する方を使う）
        title = None
        if i_di["paper"] and not i_di["verified_paper"]:
            title = i_di["paper"]["title"]
        elif not i_di["paper"] and i_di["verified_paper"]:
            title = i_di["verified_paper"]["title"]
        elif i_di["paper"] and i_di["verified_paper"]:
            title = i_di["paper"]["title"]
        else:
            continue

        if title not in seen_titles:
            seen_titles.append(title)

        # 正規化
        title_norm = normalize_title(title)
        # if title_norm not in papers_title_list:
        #     papers_title_list.append(title_norm)
            # 負例追加用
        if title_norm not in papers_title_norm_list:
            papers_title_norm_list.append(title_norm)   
            papers_title_list.append(title)     

    # 正規化後の重複チェック
    for t in seen_titles:
        t_norm = normalize_title(t)
        if t_norm in norm_seen:
            print("dup title:", t_norm, t)
        else:
            norm_seen.append(t_norm)

    print("before norm", len(seen_titles))
    return papers_title_list

def making_title_url_dict(dataset: list[dict], papers_title_list: list[str]) -> dict[str, list[str]]:
    """タイトルに対応する homepage URL を dict にまとめる"""
    title_url_dict: dict[str, list[str]] = {}

    for title in papers_title_list:
        url_list = []
        norm_title = normalize_title(title)     # 負例追加用
        for i_di in dataset:
            paper = i_di.get("paper")
            verified_paper = i_di.get("verified_paper")

            paper_title = normalize_title(paper.get("title")) if paper else ""
            verified_title = normalize_title(verified_paper.get("title")) if verified_paper else ""

            # if (title == paper_title or title == verified_title):
            if (norm_title == paper_title or norm_title == verified_title):       # 負例追加用
                homepage = i_di.get("homepage")
                if homepage:
                    url_list.append(homepage)
        # if url_list:
        title_url_dict[title] = url_list
    print("title_url_dict:", len(title_url_dict))
    return title_url_dict

def check_produce_url(extracted_url_di: dict, nozero_title_url_dict: dict):
    """抽出URLとデータセットのURLを比較し、produce / non_produce を分類"""
    title_match_count = 0
    not_match_title_list = []
    produce_dict = {}
    non_produce_dict = {}
    count_produce_url = 0
    count_nonproduce_url = 0
    empty_extraction_url = []

    
    for k_ex, v_ex in extracted_url_di.items():
        k_ex_norm = normalize_title(k_ex)
        found = False  # 一度もマッチしなかったか確認するフラグ

        if v_ex == []:
            empty_extraction_url.append(k_ex)
            continue

        for k_da, v_da in nozero_title_url_dict.items():
            k_da_norm = normalize_title(k_da)
            produce_url_list = []
            non_produce_url_list = []

            # ★ 双方向部分一致に変更
            if k_ex_norm == k_da_norm:
                title_match_count += 1
                found = True
                for i_da in v_da:
                    for i_ex in v_ex:
                        if normalize_title(i_da) == normalize_title(i_ex):
                            produce_url_list.append(i_da)
                        else:
                            non_produce_url_list.append(i_ex)
                
                if produce_url_list:
                    produce_dict[k_da] = produce_url_list
                    count_produce_url += len(produce_url_list)
                if non_produce_url_list:
                    # non_produce_dict[k_da] = non_produce_url_list
                    non_produce_dict[k_da_norm] = non_produce_url_list   # 負例追加用
                    count_nonproduce_url += len(non_produce_url_list)
                break
        if not found:
            not_match_title_list.append(k_ex_norm)
            # not_match_title_list.append(k_ex)       # pdfダウンロード用

    print("タイトル一致数:", title_match_count)
    print("マッチしなかったタイトル数/データセットURLが登録されていない数:", len(not_match_title_list))
    # print("not matched titles:", not_match_title_list[:20])  # 確認用に先頭20件だけ出すと便利
    print("ProduceのURLの数：",count_produce_url)
    print("non-ProduceのURLの数：",count_nonproduce_url)
    print("URL抽出されなかったタイトル数:", len(empty_extraction_url))
    
    count_nonproduce = 0
    negative_example_dict = {}
    for k in produce_dict.keys():
        norm_k = normalize_title(k)
        if norm_k in non_produce_dict.keys():
            count_nonproduce += len(non_produce_dict[norm_k])
            negative_example_dict[k] = non_produce_dict[norm_k]
    print("negative_example_dictの論文数:", len(negative_example_dict))
    print("2672個のうちnon-produceのURLが存在する論文数:", count_nonproduce)
    # return negative_example_dict     # 負例追加用
    return produce_dict,negative_example_dict      # 正例＋負例追加用
    # return [produce_dict, non_produce_dict]
    # return not_match_title_list     # PDFダウンロード用

if __name__ == '__main__':
    main()
