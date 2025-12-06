from typing import List
from fastapi import FastAPI, UploadFile, File
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

from invoice_qc.models import Invoice
from invoice_qc.extractor import (
    extract_text_from_pdf,
    extract_text_from_image,
    parse_raw_invoice,
)
from invoice_qc.validator import validate_invoices
from invoice_qc.gemini_fallback import _call_gemini

# Load .env settings (for GEMINI_API_KEY)
load_dotenv()

# -------------------------------------------------------------------
# FastAPI App
# -------------------------------------------------------------------
app = FastAPI(title="Invoice QC Service", version="1.0.0")


# -------------------------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------------------------
@app.get("/health")
def health():
    return {"status": "ok", "gemini_key_loaded": bool(os.getenv("GEMINI_API_KEY"))}


# -------------------------------------------------------------------
# OCR STATUS CHECK
# -------------------------------------------------------------------
@app.get("/ocr-status")
def ocr_status():
    """Check whether OCR libraries (Pillow + pytesseract) are importable.
    Native Tesseract installation is still required for real OCR.
    """
    try:
        import pytesseract  # noqa
        from PIL import Image  # noqa
        return {"ocr_available": True}
    except Exception:
        return {"ocr_available": False}


# -------------------------------------------------------------------
# VALIDATE JSON (for API clients)
# -------------------------------------------------------------------
@app.post("/validate-json")
def validate_json(invoices: List[Invoice]):
    results, summary = validate_invoices(invoices)

    return {
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }


# -------------------------------------------------------------------
# EXTRACT + VALIDATE PDFs & IMAGES
# Used by Streamlit UI
# -------------------------------------------------------------------
@app.post("/extract-and-validate-pdfs")
async def extract_and_validate_pdfs(files: List[UploadFile] = File(...)):
    invoices: List[Invoice] = []

    for f in files:
        import tempfile
        from pathlib import Path

        # Save uploaded file temporarily
        suffix = Path(f.filename).suffix.lower()
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            file_bytes = await f.read()
            tmp.write(file_bytes)
            tmp_path = Path(tmp.name)

        # Select extraction mode based on file extension
        if suffix in [".jpg", ".jpeg", ".png"]:
            raw_text = extract_text_from_image(tmp_path)
        else:
            raw_text = extract_text_from_pdf(tmp_path)

        # Parse extracted text into invoice structured format
        invoice = parse_raw_invoice(raw_text)
        invoices.append(invoice)

        # Remove temp file
        tmp_path.unlink(missing_ok=True)

    # Apply validation rules
    results, summary = validate_invoices(invoices)

    return {
        "summary": summary.model_dump(),
        "invoices": [inv.model_dump() for inv in invoices],
        "results": [r.model_dump() for r in results],
    }


# -------------------------------------------------------------------
# CHAT ENDPOINT — AI ANSWERS ABOUT THE INVOICE
# -------------------------------------------------------------------

class ChatDirectRequest(BaseModel):
    invoices: list
    summary: dict
    question: str


@app.post("/chat-direct")
def chat_direct(req: ChatDirectRequest):
    """
    Multilingual invoice chatbot:
    - Uses only invoice JSON + summary provided by user
    - Responds in user's question language
    - Uses Gemini for reasoning
    """

    prompt = f"""
You are a multilingual invoice assistant.
You must answer ONLY using the invoice data provided.

If information is missing, say:
"Information not found in the invoices."

Always answer in the SAME LANGUAGE as the user's question.

-----------------------------------------------------
📄 INVOICES (JSON):
{json.dumps(req.invoices, indent=2, ensure_ascii=False)}

📊 SUMMARY:
{json.dumps(req.summary, indent=2, ensure_ascii=False)}

❓ USER QUESTION:
{req.question}
-----------------------------------------------------

Provide a clear and concise answer.
"""

    answer = _call_gemini(prompt)

    if not answer:
        return {
            "answer": "❌ Gemini API failed. Check your API key or backend logs."
        }

    return {"answer": answer}
