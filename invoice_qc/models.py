# invoice_qc/models.py
from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel


class RawInvoice(BaseModel):
    full_text: str
    language: str
    file_name: str


class LineItem(BaseModel):
    description: str
    quantity: Optional[float] = None
    unit_price: Optional[float] = None
    line_total: Optional[float] = None


class Invoice(BaseModel):
    invoice_number: Optional[str]
    invoice_date: Optional[str]  # ISO date string
    due_date: Optional[str] = None

    seller_name: Optional[str]
    buyer_name: Optional[str]

    currency: Optional[str] = None
    net_total: Optional[float] = None
    tax_amount: Optional[float] = None
    gross_total: Optional[float] = None

    payment_terms: Optional[str] = None
    external_reference: Optional[str] = None

    line_items: List[LineItem] = []
    language: Optional[str] = None
    file_name: Optional[str] = None


class InvoiceValidationResult(BaseModel):
    invoice_id: str
    is_valid: bool
    errors: List[str]


class BatchValidationSummary(BaseModel):
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    error_counts: dict
