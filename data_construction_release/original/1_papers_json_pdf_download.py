import os
import re
import json
import requests
import time
import making_dataset
import making_dataset_produce_or_not_url_classify

FAILED_JSON = "parthit_compare_dataset_paper_with_abstract_failed_download.json"
NO_URL_JSON = "parthit_compare_dataset_paper_with_abstract_no_url.json"
NOT_FOUND_JSON = "parthit_compare_dataset_paper_with_abstract_not_found.json"
MANY_MATCH_JSON = "parthit_compare_dataset_paper_with_abstract_many_match.json"
S2_API_KEY = os.getenv('S2_API_KEY')
result_limit = 1
PDF_DIR = "compare_dataset_paper_with_abstract_failed_download_pdfs"
os.makedirs(PDF_DIR, exist_ok=True)
no_pdf_url_list = []
failed_download_pdf_list = []
count_paper_pdf = 0
count_no_pdf_url = 0
count_pdf_url = 0
count_failed_download_pdf =0
not_found_papers_list = []
id = 0
def main():
    dataset_papers_li = reading_papers_json()
    check_pdf_url(dataset_papers_li)
    global no_pdf_url_list,count_paper_pdf,count_no_pdf_url, count_pdf_url,count_failed_download_pdf
    dataset_li = making_dataset.reading_json()
    papers_title_list = making_dataset.paper_verified_paper_nodup(dataset_li)     # dataset_liに登録されている論文タイトルの重複なしリストを作る
    # papers_title_list = []

#＝＝＝ 最初の実行で見つからなかった論文リストの読み込み＝＝＝
    # with open("/workspace/second_compare_dataset_paper_with_abstract_not_found.json") as f:
    #     dataset_li:list[dict] = json.load(f)
    # for i in dataset_li:
    #     papers_title_list.append(i["title"])
    # print(len(papers_title_list))
# =============================================================

    # found_papers(papers_norm_title_list,dataset_papers_li)
    # papers_title_list = []
    # for i in dataset_li:
    #     papers_title_list.append(making_dataset_produce_or_not_url_classify.normalize_title(i["title"]))

    # dataset_li = making_dataset_produce_or_not_url_classify.reading_dataset_json()
    # extracted_url_di = making_dataset_produce_or_not_url_classify.reading_extracted_urls_json()
    # print("extracted_urls.json の数:", len(extracted_url_di.keys()))
    # papers_title_list = making_dataset_produce_or_not_url_classify.paper_verified_paper_nodup(dataset_li)
    # print("正規化後タイトル数:", len(papers_title_list))
    # title_url_dict = making_dataset_produce_or_not_url_classify.making_title_url_dict(dataset_li, papers_title_list)

    # papers_title_list = making_dataset_produce_or_not_url_classify.check_produce_url(extracted_url_di, title_url_dict)
    count_papers(papers_title_list,dataset_papers_li)
    found_papers(papers_title_list,dataset_papers_li)
    # print(f"urlがない論文リスト：{no_pdf_url_list}")
    # print(len(no_pdf_url_list))
    # print(f"ダウンロードに失敗した論文リスト：{failed_download_pdf_list}")
    # print(f"Semantic Scholarにない論文リスト：{not_found_papers_list}")
    # print(f"Semantic Scholarにない論文数：{len(not_found_papers_list)}")
    # print(f"Semantic Scholarにない論文数：{count_paper_pdf}")
    # print(f"URLのない論文PDF：{count_no_pdf_url}")
    # print(f"URLがある論文PDF：{count_pdf_url}")
    # print(f"ダウンロードに失敗した論文PDF：{count_failed_download_pdf}")
    # print(f"ダウンロードに成功した論文PDF：{count_pdf_url-count_failed_download_pdf}")

def reading_papers_json():
    with open("/workspace/papers-with-abstracts_JST202508081105.json") as f:
        dataset_li:list[dict] = json.load(f)
    return dataset_li

def check_pdf_url(dataset:list):
    url_pdfs_list = 0
    conference_url_pdfs_list = 0
    for i in range(0,len(dataset)):
        if dataset[i]["url_pdf"]:
            url_pdfs_list += 1
        if dataset[i]["conference_url_pdf"]:
            conference_url_pdfs_list += 1
    print(len(dataset))
    print(f"url_pdf：{url_pdfs_list}")
    print(f"conference_url_pdf：{conference_url_pdfs_list}")

def count_papers(titles:list, papers:list):
    count = 0
    url_count = 0
    conference_count = 0
    for title in titles:
        for paper in papers:
            if title == paper["title"]:
                count += 1
                if paper["url_pdf"]:
                    url_count += 1
                if paper["conference_url_pdf"]:
                    conference_count += 1
                break
    print("全論文数",len(titles))
    print("jsonファイルに存在する論文数：",count)
    print("urlがある数：",url_count)
    print("conference_urlがある数：",conference_count)

def found_papers(titles:list, papers:list):
    """titlesリストから一致する論文を探してダウンロードする"""
    global id
    for title in titles:
        id += 1
        matched_papers = []
        # 正規化
        # for p in papers:
        #     norm_p_title = making_dataset_produce_or_not_url_classify.normalize_title(p["title"])
        #     if title == norm_p_title:
        #         matched_papers.append(p)
        # 普通
        # for p in papers:
        #     if title == p["title"]:
        #         matched_papers.append(p)
        # 部分一致
        for p in papers:
            if p["title"]:
                if title in p["title"] or p["title"] in title:
                    matched_papers.append(p)

        if len(matched_papers) == 1:
            print(f"\n{id}=== Found {len(matched_papers)} paper(s) for: {title} ===")
            print_papers(matched_papers)
        elif len(matched_papers) > 1:
            print(f"Many match papers:{title}")
            save_many_match_papers(title)
        else:
            print(f"Not found in JSON: {title}")
            save_not_found_papers(title)


def print_papers(papers):
    for idx, paper in enumerate(papers):
        print(f"{idx}  {paper['title']} {paper['url_pdf']}")
        download_pdf(paper)

def save_failed_download(title, url):
    """失敗したPDFをJSONに追記保存"""
    data = {"title": title, "url": url}
    try:
        if os.path.exists(FAILED_JSON):
            with open(FAILED_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open(FAILED_JSON, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ JSON保存失敗: {e}")

def save_no_pdf_url(title):
    """urlのないPDFをJSONに追記保存"""
    data = {"title": title}
    try:
        if os.path.exists(NO_URL_JSON):
            with open(NO_URL_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open(NO_URL_JSON, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ JSON保存失敗: {e}")

def save_not_found_papers(title):
    """Semantic Scholarで見つからなかったPDFをJSONに追記保存"""
    data = {"title": title}
    try:
        if os.path.exists(NOT_FOUND_JSON):
            with open(NOT_FOUND_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open(NOT_FOUND_JSON, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ JSON保存失敗: {e}")

def save_many_match_papers(title):
    """部分一致で２つ以上見つかった論文を保存"""
    data = {"title": title}
    try:
        if os.path.exists(MANY_MATCH_JSON):
            with open(MANY_MATCH_JSON, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []
        existing.append(data)
        with open(MANY_MATCH_JSON, "w", encoding="utf-8") as f:
            json.dump(existing, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"⚠ JSON保存失敗: {e}")

def download_pdf(paper):
    pdf_info = paper.get("url_pdf")
    global no_pdf_url_list,count_paper_pdf,count_no_pdf_url, count_pdf_url,count_failed_download_pdf,failed_download_pdf_list
    count_paper_pdf += 1
    if not pdf_info:
        print("No PDF available.")
        count_no_pdf_url += 1
        no_pdf_url_list.append(paper.get("title"))
        save_no_pdf_url(paper.get("title"))
        return
    count_pdf_url += 1
    pdf_url = pdf_info
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", paper["title"])
    filepath = os.path.join(PDF_DIR, f"{safe_title}.pdf")

    # 既に存在していたらスキップ
    if os.path.exists(filepath):
        print(f"Already downloaded: {filepath}")
        return

    try:
        rsp = requests.get(pdf_url)
        if rsp.status_code == 200 and rsp.headers.get("Content-Type", "").startswith("application/pdf"):
            with open(filepath, "wb") as f:
                f.write(rsp.content)
            print(f"Downloaded PDF: {filepath}")
        else:
            count_failed_download_pdf += 1
            failed_download_pdf_list.append(paper.get("title"))
            save_failed_download(paper.get("title"), pdf_url)
            print(f"Failed to download PDF: {pdf_url}")
    except Exception as e:
        count_failed_download_pdf += 1
        failed_download_pdf_list.append(paper.get("title"))
        save_failed_download(paper.get("title"), pdf_url)
        print(f"Error downloading {pdf_url}: {e}")

if __name__ == '__main__':
    main()