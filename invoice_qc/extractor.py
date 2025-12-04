# invoice_qc/extractor.py
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pdfplumber

from .config import (
	LABEL_PATTERNS,
	DATE_PATTERNS,
	ALLOWED_CURRENCIES,
	AMOUNT_PATTERN,
)
from .models import Invoice, LineItem


@dataclass
class RawInvoiceText:
	path: Path
	full_text: str


def extract_text_from_pdf(pdf_path: Path) -> RawInvoiceText:
	parts: List[str] = []
	with pdfplumber.open(str(pdf_path)) as pdf:
		for page in pdf.pages:
			parts.append(page.extract_text() or "")
	return RawInvoiceText(path=pdf_path, full_text="\n".join(parts))


def _parse_date_from_text(text: str) -> Optional[str]:
	if not text:
		return None

	for pattern in DATE_PATTERNS:
		m = pattern.search(text)
		if not m:
			continue
		groups = m.groups()
		if len(groups) != 3:
			continue

		if len(groups[0]) == 4:
			year, month, day = groups
		else:
			day, month, year = groups

		try:
			dt = datetime(int(year), int(month), int(day))
			return dt.date().isoformat()
		except ValueError:
			continue

	return None


def _parse_amount(s: str) -> Optional[float]:
	if not s:
		return None
	m = AMOUNT_PATTERN.search(s)
	if not m:
		return None
	val = m.group(0).replace(",", "")
	try:
		return float(val)
	except ValueError:
		return None


def _extract_single_field(text: str, key: str) -> Optional[str]:
	patterns = LABEL_PATTERNS.get(key, [])
	for pattern in patterns:
		for line in text.splitlines():
			m = pattern.search(line)
			if m:
				return m.groups()[-1].strip()
	return None


def _guess_currency(text: str) -> Optional[str]:
	val = _extract_single_field(text, "currency")
	if val and val.upper() in ALLOWED_CURRENCIES:
		return val.upper()

	for cur in ALLOWED_CURRENCIES:
		if re.search(rf"\b{cur}\b", text):
			return cur
	return None


def _extract_line_items(text: str) -> List[LineItem]:
	"""
	Naive line-item parser:
	- Find header line with 'Description' and 'Qty'/'Quantity'
	- Parse subsequent lines split by 2+ spaces
	- Stop when 'Grand Total' appears
	"""
	lines = [l for l in text.splitlines() if l.strip()]
	header_idx = None

	for i, line in enumerate(lines):
		low = line.lower()
		if "description" in low and ("qty" in low or "quantity" in low):
			header_idx = i
			break

	if header_idx is None:
		return []

	items: List[LineItem] = []
	for line in lines[header_idx + 1 :]:
		low = line.lower()
		if "grand" in low and "total" in low:
			break

		parts = re.split(r"\s{2,}", line.strip())
		if not parts:
			continue

		description = parts[0]
		qty = _parse_amount(parts[1]) if len(parts) > 1 else None
		unit_price = _parse_amount(parts[2]) if len(parts) > 2 else None
		line_total = _parse_amount(parts[3]) if len(parts) > 3 else None

		items.append(
			LineItem(
				description=description,
				quantity=qty,
				unit_price=unit_price,
				line_total=line_total,
			)
		)

	return items


def parse_raw_invoice(raw: RawInvoiceText) -> Invoice:
	text = raw.full_text

	invoice_number_raw = _extract_single_field(text, "invoice_number") or raw.path.stem

	invoice_date_raw = _extract_single_field(text, "invoice_date") or text
	invoice_date_str = _parse_date_from_text(invoice_date_raw)
	if invoice_date_str is None:
		invoice_date_str = datetime.today().date().isoformat()

	due_date_raw = _extract_single_field(text, "due_date")
	due_date_str = _parse_date_from_text(due_date_raw) if due_date_raw else None

	seller_name = _extract_single_field(text, "seller_name") or "UNKNOWN_SELLER"
	buyer_name = _extract_single_field(text, "buyer_name") or "UNKNOWN_BUYER"

	currency = _guess_currency(text) or "INR"

	net_total = None
	for pat in LABEL_PATTERNS.get("net_total", []):
		m = pat.search(text)
		if m:
			net_total = _parse_amount(m.group(1))
			if net_total is not None:
				break

	tax_amount = None
	for pat in LABEL_PATTERNS.get("tax_amount", []):
		m = pat.search(text)
		if m:
			tax_amount = _parse_amount(m.group(2))
			if tax_amount is not None:
				break

	gross_total = None
	for pat in LABEL_PATTERNS.get("gross_total", []):
		m = pat.search(text)
		if m:
			gross_total = _parse_amount(m.group(1))
			if gross_total is not None:
				break

	line_items = _extract_line_items(text)

	return Invoice(
		invoice_number=invoice_number_raw,
		invoice_date=datetime.fromisoformat(invoice_date_str).date(),
		due_date=datetime.fromisoformat(due_date_str).date() if due_date_str else None,
		seller_name=seller_name,
		buyer_name=buyer_name,
		currency=currency,
		net_total=net_total,
		tax_amount=tax_amount,
		gross_total=gross_total,
		line_items=line_items,
	)


def extract_invoices_from_dir(pdf_dir: str) -> List[Invoice]:
	base = Path(pdf_dir)
	pdf_files = sorted(base.glob("*.pdf"))
	invoices: List[Invoice] = []
	for pdf_path in pdf_files:
		raw = extract_text_from_pdf(pdf_path)
		inv = parse_raw_invoice(raw)
		invoices.append(inv)
	return invoices


def export_invoices_to_json(invoices: List[Invoice], output_path: str) -> None:
	data = [inv.model_dump() for inv in invoices]
	out = Path(output_path)
	out.write_text(json.dumps(data, indent=2, default=str), encoding="utf-8")
