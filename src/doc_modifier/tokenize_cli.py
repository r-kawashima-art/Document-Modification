"""CLI for the auto-tokenizer.

Examples::

    # Auto-detect tables and emit a tokenized template plus a starter data file:
    python -m doc_modifier.tokenize_cli \\
        --source "templates/Template_Invitation letter_Adventure India.docx" \\
        --out "templates/Template_Invitation_Letter_Adventure_India_auto.docx" \\
        --starter-data "data/_starter_invitation.xlsx"

    # Dry-run — preview the proposed plan, don't write:
    python -m doc_modifier.tokenize_cli --source path/to/source.docx --dry-run

    # Explicit mapping mode (yaml/json/xlsx):
    python -m doc_modifier.tokenize_cli \\
        --source source.docx \\
        --mapping mappings.yaml \\
        --out tokenized.docx
"""
from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from .tokenize_template import (
    analyze,
    apply,
    emit_starter_data,
    load_mapping,
    verify,
)


def _parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="doc_modifier.tokenize_cli",
        description=(
            "Auto-create a tokenized .docx template from a source document. "
            "Detects label:value tables, generates snake_case tokens, and sweeps "
            "the body for inline duplicates of table values."
        ),
    )
    p.add_argument("--source", required=True, type=Path, help="Source .docx file to tokenize.")
    p.add_argument("--out", type=Path, help="Output tokenized .docx path (required unless --dry-run).")
    p.add_argument(
        "--mapping",
        type=Path,
        default=None,
        help="Optional explicit original→token mapping (.yaml / .json / .xlsx).",
    )
    p.add_argument(
        "--no-auto-detect",
        action="store_true",
        help="Disable auto-detection of label:value tables (use only the explicit mapping).",
    )
    p.add_argument(
        "--starter-data",
        type=Path,
        default=None,
        help="If provided, also emit a starter .xlsx data file with the token columns + one example row.",
    )
    p.add_argument("--dry-run", action="store_true", help="Print the plan and exit without writing.")
    p.add_argument("-v", "--verbose", action="store_true")
    return p


def _print_plan(plan) -> None:
    print(f"\nProposed {len(plan.replacements)} replacement(s):\n")
    print(f"  {'TOKEN':<32} {'LABEL':<28} ORIGINAL VALUE")
    print(f"  {'-' * 32} {'-' * 28} {'-' * 40}")
    for r in plan.replacements:
        token = "{{" + r.token + "}}"
        original = (r.original[:38] + "…") if len(r.original) > 39 else r.original
        print(f"  {token:<32} {r.label[:26]:<28} {original}")
        print(f"  {' ' * 32} {' ' * 28} @ {r.location}")
    if plan.skipped:
        print(f"\nSkipped {len(plan.skipped)} candidate(s):")
        for s in plan.skipped:
            print(f"  • {s}")
    if plan.warnings:
        print(f"\nWarnings ({len(plan.warnings)}):")
        for w in plan.warnings:
            print(f"  ⚠ {w}")


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    logging.basicConfig(level=logging.DEBUG if args.verbose else logging.INFO, format="%(message)s")

    if not args.source.exists():
        print(f"error: source not found: {args.source}", file=sys.stderr)
        return 2

    explicit_mapping = load_mapping(args.mapping) if args.mapping else None
    plan = analyze(
        args.source,
        explicit_mapping=explicit_mapping,
        auto_detect_tables=not args.no_auto_detect,
    )

    _print_plan(plan)

    if args.dry_run:
        return 0

    if not args.out:
        print("error: --out is required unless --dry-run", file=sys.stderr)
        return 2

    n = apply(args.source, plan, args.out)
    print(f"\nWrote tokenized template: {args.out}  ({n} substitutions)")

    if args.starter_data:
        path = emit_starter_data(plan, args.starter_data)
        print(f"Wrote starter data file:    {path}")

    tokens = verify(args.out)
    print(f"\nTokens present in output ({len(tokens)}): {', '.join(sorted(tokens))}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
