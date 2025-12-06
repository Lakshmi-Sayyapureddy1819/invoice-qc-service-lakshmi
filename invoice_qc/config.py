# invoice_qc/config.py
# This module re-exports from config_labels for backward compatibility
# New code should import directly from config_labels

from .config_labels import (
    ALLOWED_CURRENCIES,
    DATE_PATTERNS,
    AMOUNT_PATTERN,
    LABEL_PATTERNS,
    MIN_VALID_DATE,
    MAX_VALID_DATE,
    EPSILON,
    TABLE_HEADERS,
)

__all__ = [
    "ALLOWED_CURRENCIES",
    "DATE_PATTERNS",
    "AMOUNT_PATTERN",
    "LABEL_PATTERNS",
    "MIN_VALID_DATE",
    "MAX_VALID_DATE",
    "EPSILON",
    "TABLE_HEADERS",
]
