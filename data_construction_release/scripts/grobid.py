import requests
import glob
from tqdm import tqdm
import os  

input_files = glob.glob("data/pdf/*.pdf")
print(input_files)

input_files[0].split(".pdf")[0].split("/")[-1]

url = "http://localhost:8070/api/processFulltextDocument"

os.makedirs("data/xml", exist_ok=True)

for input_file in tqdm(input_files):
    output_file_name = input_file.split(".pdf")[0].split("/")[-1]
    output_file = f"data/xml/{output_file_name}.xml"

    with open(input_file, "rb") as f:
        files = {"input": f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(response.text)
    else:
        print("Error:", response.status_code, response.text)
    
