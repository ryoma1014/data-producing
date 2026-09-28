import re
import json
from pathlib import Path

def main():
    extract_urls_from_mmd("/mnt/c/users/okada/Desktop/松原研究室B4/研究/2025-0829-making_dataset/mmd")

def extract_urls_from_mmd(folder_path: str, output_json: str = "next_extracted_urls.json"):
    """
    指定フォルダ内の .mmd ファイルを読み込み、URLを抽出してJSONに保存する関数
    
    Parameters
    ----------
    folder_path : str
        .mmdファイルが入っているフォルダのパス
    output_json : str, optional
        出力するJSONファイル名 (デフォルト: "extracted_urls.json")
    """
    # url_pattern = re.compile(r'\b[a-zA-Z][a-zA-Z0-9+.-]*://[^\s)>\]}]+')      # スキームあり
    url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))')
    # url_pattern = re.compile(
    #     r'\b(?:[a-zA-Z][a-zA-Z0-9+.-]*://[^\s)>\]}]+|'      # スキームあり
    #     r'(?:[a-zA-Z0-9-]+\.)+[a-zA-Z]{2,}(?:/[^\s)>\]}]*)?)' # スキームなし, URLでないものも抽出してしまう
    # )
    folder = Path(folder_path)
    results = {}

    for file_path in folder.glob("*.mmd"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        urls = url_pattern.findall(content)
        urls = [modify_url(url[0], content) for url in urls]
        urls = list(dict.fromkeys(clean_urls(urls)))
        results[file_path.stem] = urls

    with open(output_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"====URLを {output_json} に保存しました！====")
    return results

def clean_urls(urls: list) -> list:
    # 末尾のよくある句読点や括弧を取り除く
    only_urls = []
    for url in urls:
        only_urls.append(url.strip(".,;:\"'()[]。，、"))
    return only_urls

def modify_url(url: str, text: str) -> str:
    start = text.find(url)
    span = [start, start + len(url)]

    while True:
        if ' ' not in text[span[1]:]:
            if span[1] < len(text):
                if '/' in text[span[1]:]:
                    span[1] = len(text)
            break
        else:
            m = list(re.finditer(r' ', text[span[1]:]))
            m = [i.span()[0] + span[1] for i in m]
            if len(m) == 1:
                m = m + [len(text)]
            if '/' in text[m[0]:m[1]]:
                span[1] = m[1]
                continue
            break

    return text[span[0]:span[1]]


if __name__ == '__main__':
    main()