"""Command-line interface.

Examples::

    python -m doc_modifier \\
        --template templates/Template_Invitation_Letter_Adventure_India_tokenized.docx \\
        --data data/sample_data.xlsx \\
        --out output/ \\
        --formats docx,pdf

    # Inspect which tokens a template defines:
    python -m doc_modifier --template path/to/template.docx --list-tokens
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from . import docx_replacer, xlsx_replacer
from .pipeline import run


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="doc_modifier",
        description="Replace {{tokens}} in Word/Excel templates with rows from an Excel data file.",
    )
    p.add_argument("--template", required=True, type=Path, help="Path to the .docx or .xlsx template.")
    p.add_argument("--data", type=Path, help="Path to the .xlsx data file (required unless --list-tokens).")
    p.add_argument(
        "--out",
        type=Path,
        default=Path("output"),
        help="Output directory (default: ./output).",
    )
    p.add_argument(
        "--formats",
        default="docx",
        help="Comma-separated subset of {docx,xlsx,pdf}. Default: docx. Append 'pdf' to also export PDF.",
    )
    p.add_argument("--sheet", default=None, help="Sheet name inside the data .xlsx (default: active sheet).")
    p.add_argument("--list-tokens", action="store_true", help="Print the tokens referenced by the template and exit.")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    if args.list_tokens:
        ext = args.template.suffix.lower()
        tokens = (
            docx_replacer.find_tokens(args.template) if ext == ".docx" else xlsx_replacer.find_tokens(args.template)
        )
        for t in sorted(tokens):
            print(t)
        return 0

    if args.data is None:
        print("error: --data is required unless --list-tokens", file=sys.stderr)
        return 2

    formats = tuple(s.strip().lower() for s in args.formats.split(",") if s.strip())
    results = run(args.template, args.data, args.out, formats=formats, sheet=args.sheet)

    print(f"Rendered {len(results)} document(s) into {args.out}/")
    for r in results:
        line = f"  [{r.row_index}] {r.primary_out.name}  ({r.substitutions} substitutions)"
        if r.pdf_out:
            line += f"  +PDF: {r.pdf_out.name}"
        print(line)
        for w in r.warnings:
            print(f"      ⚠ {w}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
