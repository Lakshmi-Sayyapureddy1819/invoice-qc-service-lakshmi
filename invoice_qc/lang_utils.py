# invoice_qc/lang_utils.py
from __future__ import annotations
import re
from typing import Optional
from langdetect import detect
import dateparser

AMOUNT_TOKEN = r"[-+]?\d{1,3}(?:[.,\s]\d{3})*(?:[.,]\d+)?"
AMOUNT_RE = re.compile(AMOUNT_TOKEN)


def detect_language(text: str) -> str:
    try:
        return detect(text)
    except Exception:
        return "unknown"


def normalize_amount(raw: str | None) -> Optional[float]:
    if not raw:
        return None
    s = raw.strip()
    # remove currency symbols + spaces
    s = re.sub(r"[^\d.,\-]", "", s)

    if "," in s and "." in s:
        s = s.replace(".", "").replace(",", ".")
    elif "," in s and "." not in s:
        s = s.replace(",", ".")

    m = AMOUNT_RE.search(s)
    if not m:
        return None
    try:
        return float(m.group(0))
    except ValueError:
        return None


def parse_date_any(text: str | None) -> Optional[str]:
    if not text:
        return None
    dt = dateparser.parse(
        text,
        settings={"DATE_ORDER": "DMY", "PREFER_DAY_OF_MONTH": "first"},
    )
    if not dt:
        return None
    return dt.date().isoformat()


def clean_line(line: str) -> str:
    return line.strip().replace("\u00a0", " ")

# Compatibility shims: older code expects clean_text and extract_lines
def clean_text(text: str) -> str:
    """Return cleaned text for the whole document."""
    return "\n".join(clean_line(l) for l in text.splitlines())


def extract_lines(text: str) -> list[str]:
    """Split text into cleaned non-empty lines."""
    return [l for l in (clean_line(x) for x in text.splitlines()) if l]
