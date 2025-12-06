# invoice_qc/config_labels.py
"""Label patterns and configuration for field extraction from invoices."""
from __future__ import annotations

import re
from datetime import date

ALLOWED_CURRENCIES = {"INR", "EUR", "USD", "GBP"}

# Date patterns: adjust after seeing real PDFs
DATE_PATTERNS = [
    # DD/MM/YYYY or D/M/YYYY
    re.compile(r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{4})\b"),
    # YYYY-MM-DD
    re.compile(r"\b(\d{4})-(\d{1,2})-(\d{1,2})\b"),
    # Month names: Jan, Feb, etc.
    re.compile(r"\b(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{4})\b", re.IGNORECASE),
]

# Generic amount with commas & decimals
AMOUNT_PATTERN = re.compile(r"[-+]?\d{1,3}(?:,\d{3})*(?:\.\d+)?")

# Comprehensive label patterns for field extraction
LABEL_PATTERNS = {
    "invoice_number": [
        re.compile(r"Invoice\s*(No\.?|Number|#|ID)\s*[:\-]?\s*([A-Za-z0-9\-\/\.]+)", re.I),
        re.compile(r"INV[:\-\s]*([A-Za-z0-9\-\/\.]+)", re.I),
    ],
    "invoice_date": [
        re.compile(r"Invoice\s*Date\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
        re.compile(r"Date\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
    ],
    "due_date": [
        re.compile(r"Due\s*Date\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
        re.compile(r"Payment\s*Due\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
    ],
    "seller_name": [
        re.compile(r"(?:Seller|Vendor|From|Bill\s*From)\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
        re.compile(r"Company\s*(?:Name)?\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
    ],
    "seller_tax_id": [
        re.compile(r"(?:Seller|Vendor)\s*(?:Tax|GST|VAT|TIN)\s*(?:ID)?\s*[:\-]?\s*([A-Za-z0-9]+)", re.I),
    ],
    "buyer_name": [
        re.compile(r"(?:Buyer|Customer|Bill\s*To|Ship\s*To)\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
        re.compile(r"(?:To|Sold\s*To)\s*[:\-]?\s*(.+?)(?=\n|$)", re.I),
    ],
    "buyer_tax_id": [
        re.compile(r"(?:Buyer|Customer)\s*(?:Tax|GST|VAT|TIN)\s*(?:ID)?\s*[:\-]?\s*([A-Za-z0-9]+)", re.I),
    ],
    "currency": [
        re.compile(r"Currency\s*[:\-]?\s*([A-Z]{3})", re.I),
        re.compile(r"\b(INR|USD|EUR|GBP)\b", re.I),
    ],
    "net_total": [
        re.compile(r"Subtotal\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Net\s*Total\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Taxable\s*Amount\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
    "tax_amount": [
        re.compile(r"(?:CGST|SGST|IGST|GST|Tax)\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"(?:VAT|Sales\s*Tax)\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
    "gross_total": [
        re.compile(r"Total\s*(?:Payable|Amount|Due)\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Grand\s*Total\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
        re.compile(r"Final\s*Total\s*[:\-]?\s*(" + AMOUNT_PATTERN.pattern + ")", re.I),
    ],
}

MIN_VALID_DATE = date(2000, 1, 1)
MAX_VALID_DATE = date(2100, 1, 1)

EPSILON = 0.01  # Float comparison tolerance

# Table extraction hints
TABLE_HEADERS = {
    "line_items": [
        r"(?:Item|Description|Product|Service)",
        r"(?:Qty|Quantity|Units)",
        r"(?:Unit\s*Price|Rate|Price\s*Per\s*Unit)",
        r"(?:Amount|Total|Line\s*Total)",
    ]
}
