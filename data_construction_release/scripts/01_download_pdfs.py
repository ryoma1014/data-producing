import os
import re
import json
import requests
import making_dataset

FAILED_JSON = "data/logs/failed_download.json"
NO_URL_JSON = "data/logs/no_url.json"
NOT_FOUND_JSON = "data/logs/not_found.json"
MANY_MATCH_JSON = "data/logs/many_match.json"
PDF_DIR = "data/pdf"
os.makedirs(PDF_DIR, exist_ok=True)
os.makedirs("data/logs", exist_ok=True)
id = 0
counts = {"not_found": 0, "many_match": 0, "no_url": 0, "already": 0, "download": 0}
def main():
    dataset_papers_li = reading_papers_json()
    check_pdf_url(dataset_papers_li)
    dataset_li = making_dataset.reading_json()
    papers_title_list = making_dataset.paper_verified_paper_nodup(dataset_li)[:20]     # dataset_liに登録されている論文タイトルの重複なしリストを作る
    count_papers(papers_title_list,dataset_papers_li)
    found_papers(papers_title_list,dataset_papers_li)
    print_counts()


def reading_papers_json():
    with open("data/input/papers-with-abstracts_JST202508081105.json") as f:
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

        for p in papers:
            if title == p["title"]:
                matched_papers.append(p)

        if len(matched_papers) == 1:
            print(f"\n{id}=== Found {len(matched_papers)} paper(s) for: {title} ===")
            print_papers(matched_papers)
        elif len(matched_papers) > 1:
            print(f"Many match papers:{title}")
            counts["many_match"] += 1
            save_many_match_papers(title)
        else:
            print(f"Not found in JSON: {title}")
            counts["not_found"] += 1
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
    """論文JSONで見つからなかった論文をJSONに追記保存"""
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
    pdf_url = paper.get("url_pdf")
    if not pdf_url:
        print("No PDF available.")
        counts["no_url"] += 1
        save_no_pdf_url(paper.get("title"))
        return
    safe_title = re.sub(r'[\\/*?:"<>|]', "_", paper["title"])
    filepath = os.path.join(PDF_DIR, f"{safe_title}.pdf")

    # 既に存在していたらスキップ
    if os.path.exists(filepath):
        print(f"Already downloaded: {filepath}")
        counts["already"] += 1
        return

    counts["download"] += 1

    try:
        rsp = requests.get(pdf_url)
        if rsp.status_code == 200 and rsp.headers.get("Content-Type", "").startswith("application/pdf"):
            with open(filepath, "wb") as f:
                f.write(rsp.content)
            print(f"Downloaded PDF: {filepath}")
        else:
            save_failed_download(paper.get("title"), pdf_url)
            print(f"Failed to download PDF: {pdf_url}")
    except Exception as e:
        save_failed_download(paper.get("title"), pdf_url)
        print(f"Error downloading {pdf_url}: {e}")

def print_counts():
    """found_papers の結果の内訳を表示"""
    print("\n=== 集計 ===")
    print("JSONに見つからない：", counts["not_found"])
    print("部分一致で複数ヒット：", counts["many_match"])
    print("PDFのURLなし：", counts["no_url"])
    print("ダウンロード済みでスキップ：", counts["already"])
    print("ダウンロード対象：", counts["download"])

if __name__ == '__main__':
    main()