# invoice_qc/models.py
from __future__ import annotations

from datetime import date
from typing import List, Optional
from pydantic import BaseModel, Field, validator


class LineItem(BaseModel):
    description: str = Field(..., description="Description of the product/service")
    quantity: Optional[float] = Field(None, description="Quantity ordered")
    unit_price: Optional[float] = Field(None, description="Price per unit")
    line_total: Optional[float] = Field(None, description="Total price for this line")

    from pydantic import field_validator

    @field_validator("quantity", "unit_price", "line_total")
    def non_negative(cls, v, info):
        if v is not None and v < 0:
            raise ValueError(f"{info.field_name} cannot be negative")
        return v


class Invoice(BaseModel):
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None

    seller_name: str
    seller_tax_id: Optional[str] = None

    buyer_name: str
    buyer_tax_id: Optional[str] = None

    currency: str
    net_total: Optional[float] = None
    tax_amount: Optional[float] = None
    gross_total: Optional[float] = None

    payment_terms: Optional[str] = None
    external_reference: Optional[str] = Field(
        None, description="PO number or external reference"
    )

    line_items: List[LineItem] = Field(default_factory=list)


class InvoiceValidationResult(BaseModel):
    invoice_id: str
    is_valid: bool
    errors: List[str] = Field(default_factory=list)


class BatchValidationSummary(BaseModel):
    total_invoices: int
    valid_invoices: int
    invalid_invoices: int
    error_counts: dict[str, int]
