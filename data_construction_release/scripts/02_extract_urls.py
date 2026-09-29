import re
import json
from pathlib import Path

def main():
    dataset_di = extract_urls_from_mmd("data/mmd")

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

            v_li[i] = url[:cut_index].strip(".,;:\"'()[]。，、")

    writing_dataset_json(dataset_di)


def extract_urls_from_mmd(folder_path: str):
    """
    指定フォルダ内の .mmd ファイルを読み込み、URLを抽出する関数
    
    Parameters
    ----------
    folder_path : str
        .mmdファイルが入っているフォルダのパス
    """

    url_pattern = re.compile(r'((https?|ftp)://(?:www\.)?[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}(?:/[^\s()]*)?(?<!\.))')

    folder = Path(folder_path)
    results = {}

    for file_path in folder.glob("*.mmd"):
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        urls = url_pattern.findall(content)
        urls = [modify_url(url[0], content) for url in urls]
        urls = list(dict.fromkeys(clean_urls(urls)))
        results[file_path.stem] = urls

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


def writing_dataset_json(dataset_di):
    with open("data/intermediate/perfect_extracted_urls.json", "w") as f:
        json.dump(dataset_di, f, indent=4, ensure_ascii=False)
    return


if __name__ == '__main__':
    main()