# app/main.py
from __future__ import annotations

from typing import List

from fastapi import FastAPI, UploadFile, File

from invoice_qc.models import Invoice
from invoice_qc.validator import validate_invoices
from invoice_qc.extractor import extract_text_from_pdf, parse_raw_invoice


app = FastAPI(title="Invoice QC Service")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/validate-json")
def validate_json(invoices: List[Invoice]):
    results, summary = validate_invoices(invoices)
    return {
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }


@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    invoices: List[Invoice] = []

    for f in files:
        import tempfile
        from pathlib import Path

        suffix = ".pdf" if not f.filename.lower().endswith(".pdf") else ""
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            content = await f.read()
            tmp.write(content)
            tmp_path = Path(tmp.name)

        raw = extract_text_from_pdf(tmp_path)
        inv = parse_raw_invoice(raw)
        invoices.append(inv)

        tmp_path.unlink(missing_ok=True)

    results, summary = validate_invoices(invoices)
    return {
        "extracted": [inv.model_dump() for inv in invoices],
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }
