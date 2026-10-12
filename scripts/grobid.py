import requests
import glob
from tqdm import tqdm
import os  
from pathlib import Path

input_files = glob.glob("data/pdf/*.pdf")
print(input_files)

url = "http://localhost:8070/api/processFulltextDocument"

os.makedirs("data/xml", exist_ok=True)

for input_file in tqdm(input_files):
    output_file_name = Path(input_file).stem
    output_file = Path("data/xml") / f"{output_file_name}.xml"

    with open(input_file, "rb") as f:
        files = {"input": f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        with open(output_file, "w", encoding="utf-8") as out:
            out.write(response.text)
    else:
        print("Error:", response.status_code, response.text)
    
