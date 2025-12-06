import requests
import json

url = "http://127.0.0.1:8000/extract-and-validate-pdfs"
import os
BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
pdf_path = os.path.join(BASE, "pdfs", "sample_pdf_1.pdf")
files = [("files", (os.path.basename(pdf_path), open(pdf_path, "rb"), "application/pdf"))]
print(f"Posting to {url}...")
r = requests.post(url, files=files, timeout=60)
print("Status:", r.status_code)
try:
    print(json.dumps(r.json(), indent=2, ensure_ascii=False))
except Exception as e:
    print("Response text:")
    print(r.text)
    raise
