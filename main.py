# main.py
from typing import List
from pathlib import Path
import tempfile
import os
import json

from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel

from invoice_qc.models import Invoice
from invoice_qc.extractor import (
    extract_text_from_pdf,
    extract_text_from_image,
    parse_raw_invoice,
)
from invoice_qc.validator import validate_invoices
from invoice_qc.gemini_fallback import _call_gemini

app = FastAPI(title="Invoice QC Service (Multilingual + AI Chat)")


# ---------------------------------------------------------
# HEALTH / OCR STATUS
# ---------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_loaded": bool(os.getenv("GEMINI_API_KEY"))}


@app.get("/ocr-status")
def ocr_status():
    """
    Just checks if Pillow + pytesseract are importable.
    Native Tesseract binary still required for real OCR of images.
    """
    try:
        import pytesseract  # noqa
        from PIL import Image  # noqa
        return {"ocr_available": True}
    except Exception:
        return {"ocr_available": False}


# ---------------------------------------------------------
# VALIDATE JSON DIRECTLY (for API / tests)
# ---------------------------------------------------------
@app.post("/validate-json")
def validate_json(invoices: List[Invoice]):
    results, summary = validate_invoices(invoices)

    return {
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }


# ---------------------------------------------------------
# EXTRACT + VALIDATE PDFs/IMAGES
# ---------------------------------------------------------
@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    invoices: List[Invoice] = []

    for f in files:
        suffix = Path(f.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(await f.read())
            tmp_path = Path(tmp.name)

        # Decide PDF vs image
        if suffix in [".jpg", ".jpeg", ".png"]:
            raw = extract_text_from_image(tmp_path)
        else:
            raw = extract_text_from_pdf(tmp_path)

        invoice = parse_raw_invoice(raw)
        invoices.append(invoice)

        tmp_path.unlink(missing_ok=True)

    results, summary = validate_invoices(invoices)

    return {
        "summary": summary.model_dump(),
        "invoices": [inv.model_dump() for inv in invoices],
        "results": [r.model_dump() for r in results],
    }


# ---------------------------------------------------------
# CHAT ENDPOINT (Multilingual AI over invoices)
# ---------------------------------------------------------
class ChatDirectRequest(BaseModel):
    invoices: list
    summary: dict
    question: str


@app.post("/chat-direct")
def chat_direct(req: ChatDirectRequest):
    """
    Multilingual invoice chatbot:
    - Uses ONLY the provided invoice JSON + summary (no external DB)
    - Responds in the SAME LANGUAGE as the user's question
    """

    prompt = f"""
You are a multilingual invoice assistant.

You must answer ONLY using the invoice data provided.
If the answer is not present in the invoices, reply:
"Information not found in the invoices."

Always respond in the SAME LANGUAGE as the user's question.

--- INVOICES (JSON) ---
{json.dumps(req.invoices, indent=2, ensure_ascii=False)}

--- SUMMARY (JSON) ---
{json.dumps(req.summary, indent=2, ensure_ascii=False)}

--- USER QUESTION ---
{req.question}
"""

    answer = _call_gemini(prompt)

    if not answer:
        return {"answer": "❌ Gemini API failed. Check your API key or backend logs."}

    return {"answer": answer}
