import requests
import glob
from tqdm import tqdm
import os  # 追加

# PDF ファイル一覧
input_files = glob.glob("/workspace/data-producing/data_construction_release/data/pdf/*.pdf")
print(input_files)

# Linux 用に安全にファイル名を取得
input_files[0].split(".pdf")[0].split("/")[-1]

# GROBID サーバーのURL
url = "http://localhost:8070/api/processFulltextDocument"

# 出力フォルダがなければ作成
os.makedirs("/mnt/ssd/研究/xml", exist_ok=True)

# 入力PDFファイル
for input_file in tqdm(input_files):

    # Linux 用にパスを修正
    output_file_name = input_file.split(".pdf")[0].split("/")[-1]
    # 出力XMLファイル
    output_file = f"/workspace/data-producing/data_construction_release/data/xml/{output_file_name}.xml"

    # PDFを送信して結果を受け取る
    with open(input_file, "rb") as f:
        files = {"input": f}
        response = requests.post(url, files=files)

    # レスポンスを保存
    if response.status_code == 200:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(response.text)
        # print(f"Saved XML to {output_file}")
    else:
        print("Error:", response.status_code, response.text)
    
    # break  # テスト用に最初の1つだけ処理
