# invoice_qc/config.py
import re
from datetime import date

ALLOWED_CURRENCIES = {"INR", "EUR", "USD", "GBP"}

# Date patterns: adjust after seeing real PDFs
DATE_PATTERNS = [
    # DD/MM/YYYY or D/M/YYYY
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"),
    # YYYY-MM-DD
    re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"),
]

# Generic amount with commas & decimals
AMOUNT_PATTERN = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")

LABEL_PATTERNS = {
    "invoice_number": [
        re.compile(r"Invoice\s*(No\.?|Number|#)\s*[:\-]?\s*(.+)", re.I)
    ],
    "invoice_date": [
        re.compile(r"Invoice\s*Date\s*[:\-]?\s*(.+)", re.I)
    ],
    "due_date": [
        re.compile(r"Due\s*Date\s*[:\-]?\s*(.+)", re.I)
    ],
    "seller_name": [
        re.compile(r"Seller\s*[:\-]?\s*(.+)", re.I),
        re.compile(r"From\s*[:\-]?\s*(.+)", re.I),
    ],
    "buyer_name": [
        re.compile(r"Buyer\s*[:\-]?\s*(.+)", re.I),
        re.compile(r"Bill\s*To\s*[:\-]?\s*(.+)", re.I),
        re.compile(r"Ship\s*To\s*[:\-]?\s*(.+)", re.I),
    ],
    "currency": [
        re.compile(r"Currency\s*[:\-]?\s*([A-Z]{3})", re.I)
    ],
    "net_total": [
        re.compile(r"Subtotal\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Net\s*Total\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
    "tax_amount": [
        re.compile(r"(GST|Tax)\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
    "gross_total": [
        re.compile(r"Total\s*Payable\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Grand\s*Total\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
}

MIN_VALID_DATE = date(2000, 1, 1)
MAX_VALID_DATE = date(2100, 1, 1)

EPSILON = 0.01  # Float comparison tolerance
