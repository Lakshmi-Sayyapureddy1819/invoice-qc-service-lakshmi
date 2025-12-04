# invoice_qc/validator.py
from __future__ import annotations

from collections import Counter
from datetime import date
from typing import Iterable, List, Tuple

from .config import ALLOWED_CURRENCIES, MIN_VALID_DATE, MAX_VALID_DATE, EPSILON
from .models import BatchValidationSummary, Invoice, InvoiceValidationResult


def _check_completeness_and_format(inv: Invoice) -> List[str]:
    errors: List[str] = []

    if not inv.invoice_number.strip():
        errors.append("missing_field: invoice_number")
    if not inv.seller_name.strip():
        errors.append("missing_field: seller_name")
    if not inv.buyer_name.strip():
        errors.append("missing_field: buyer_name")

    if not (MIN_VALID_DATE <= inv.invoice_date <= MAX_VALID_DATE):
        errors.append("format: invoice_date_out_of_range")

    if inv.due_date and inv.due_date < inv.invoice_date:
        errors.append("business_rule_failed: due_date_before_invoice_date")

    if inv.currency.upper() not in ALLOWED_CURRENCIES:
        errors.append("format: invalid_currency")

    return errors


def _check_business_rules(inv: Invoice) -> List[str]:
    errors: List[str] = []

    net = inv.net_total
    tax = inv.tax_amount
    gross = inv.gross_total

    for field_name, value in [
        ("net_total", net),
        ("tax_amount", tax),
        ("gross_total", gross),
    ]:
        if value is not None and value < 0:
            errors.append(f"business_rule_failed: {field_name}_negative")

    if net is not None and tax is not None and gross is not None:
        if abs((net + tax) - gross) > EPSILON:
            errors.append("business_rule_failed: totals_mismatch")

    if inv.line_items and net is not None:
        li_sum = sum(li.line_total or 0.0 for li in inv.line_items)
        if abs(li_sum - net) > EPSILON:
            errors.append("business_rule_failed: line_items_sum_mismatch")

    if gross is not None and gross > 1_000_000_000:
        errors.append("anomaly: total_too_large")

    return errors


def _find_duplicates(invoices: Iterable[Invoice]) -> List[Tuple[str, str, date]]:
    key_counts = Counter(
        (inv.invoice_number.strip(), inv.seller_name.strip(), inv.invoice_date)
        for inv in invoices
    )
    duplicates = [k for k, c in key_counts.items() if c > 1]
    return duplicates


def validate_invoices(
    invoices: List[Invoice],
) -> tuple[List[InvoiceValidationResult], BatchValidationSummary]:
    results: List[InvoiceValidationResult] = []

    duplicates = set(_find_duplicates(invoices))
    error_counter: Counter[str] = Counter()

    for inv in invoices:
        errors: List[str] = []

        errors.extend(_check_completeness_and_format(inv))
        errors.extend(_check_business_rules(inv))

        key = (inv.invoice_number.strip(), inv.seller_name.strip(), inv.invoice_date)
        if key in duplicates:
            errors.append("anomaly: duplicate_invoice_key")

        is_valid = len(errors) == 0
        for e in errors:
            error_counter[e] += 1

        results.append(
            InvoiceValidationResult(
                invoice_id=inv.invoice_number,
                is_valid=is_valid,
                errors=errors,
            )
        )

    total = len(invoices)
    invalid = sum(1 for r in results if not r.is_valid)
    valid = total - invalid

    summary = BatchValidationSummary(
        total_invoices=total,
        valid_invoices=valid,
        invalid_invoices=invalid,
        error_counts=dict(error_counter),
    )

    return results, summary
