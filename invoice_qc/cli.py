# invoice_qc/cli.py
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List

from .extractor import extract_invoices_from_dir, export_invoices_to_json
from .models import Invoice
from .validator import validate_invoices


def cmd_extract(args: argparse.Namespace) -> int:
    invoices = extract_invoices_from_dir(args.pdf_dir)
    export_invoices_to_json(invoices, args.output)
    print(f"Extracted {len(invoices)} invoices to {args.output}")
    return 0


def _load_invoices_from_json(path: str) -> List[Invoice]:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return [Invoice(**obj) for obj in data]


def cmd_validate(args: argparse.Namespace) -> int:
    invoices = _load_invoices_from_json(args.input)
    results, summary = validate_invoices(invoices)

    report = {
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }
    Path(args.report).write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )

    print(f"Total invoices: {summary.total_invoices}")
    print(f"Valid invoices: {summary.valid_invoices}")
    print(f"Invalid invoices: {summary.invalid_invoices}")
    if summary.error_counts:
        print("Top errors:")
        for err, count in sorted(
            summary.error_counts.items(), key=lambda kv: -kv[1]
        )[:5]:
            print(f"  {err}: {count}")

    return 0 if summary.invalid_invoices == 0 else 1


def cmd_full_run(args: argparse.Namespace) -> int:
    invoices = extract_invoices_from_dir(args.pdf_dir)
    results, summary = validate_invoices(invoices)

    report = {
        "summary": summary.model_dump(),
        "results": [r.model_dump() for r in results],
    }
    Path(args.report).write_text(
        json.dumps(report, indent=2, default=str), encoding="utf-8"
    )

    print(
        f"[FULL RUN] Total: {summary.total_invoices}, "
        f"Valid: {summary.valid_invoices}, Invalid: {summary.invalid_invoices}"
    )
    if summary.error_counts:
        print("Top errors:")
        for err, count in sorted(
            summary.error_counts.items(), key=lambda kv: -kv[1]
        )[:5]:
            print(f"  {err}: {count}")

    return 0 if summary.invalid_invoices == 0 else 1


def main() -> None:
    parser = argparse.ArgumentParser(prog="invoice-qc")
    sub = parser.add_subparsers(dest="command", required=True)

    p_extract = sub.add_parser("extract", help="Extract invoices from PDFs")
    p_extract.add_argument("--pdf-dir", required=True, help="Directory containing PDF files")
    p_extract.add_argument("--output", required=True, help="Output JSON file")
    p_extract.set_defaults(func=cmd_extract)

    p_validate = sub.add_parser("validate", help="Validate invoices from JSON")
    p_validate.add_argument("--input", required=True, help="Input JSON file")
    p_validate.add_argument("--report", required=True, help="Output validation report JSON")
    p_validate.set_defaults(func=cmd_validate)

    p_full = sub.add_parser("full-run", help="Extract + Validate")
    p_full.add_argument("--pdf-dir", required=True, help="Directory containing PDF files")
    p_full.add_argument("--report", required=True, help="Output validation report JSON")
    p_full.set_defaults(func=cmd_full_run)

    args = parser.parse_args()
    exit_code = args.func(args)
    sys.exit(exit_code)


if __name__ == "__main__":
    main()
