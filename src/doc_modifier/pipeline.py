"""End-to-end pipeline: data file + template → rendered outputs.

Usage::

    from doc_modifier.pipeline import run
    results = run(
        template="templates/Template_….docx",
        data="data/sample_data.xlsx",
        out_dir="output/",
        formats=("docx", "pdf"),
    )
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, Mapping

from . import docx_replacer, xlsx_replacer, xlsx_loader
from .pdf_exporter import PdfBackendUnavailable, to_pdf

log = logging.getLogger(__name__)


@dataclass
class RowResult:
    row_index: int
    row_data: Mapping[str, str]
    primary_out: Path
    pdf_out: Path | None = None
    substitutions: int = 0
    warnings: list[str] = field(default_factory=list)


def _sanitize(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_") or "unnamed"


def _detect_kind(template: Path) -> str:
    suffix = template.suffix.lower()
    if suffix == ".docx":
        return "docx"
    if suffix == ".xlsx":
        return "xlsx"
    raise ValueError(f"Unsupported template type: {suffix}")


def run(
    template: str | Path,
    data: str | Path,
    out_dir: str | Path,
    formats: Iterable[str] = ("docx",),
    sheet: str | None = None,
) -> list[RowResult]:
    """Render the template once per row in the data file.

    :param template: ``.docx`` or ``.xlsx`` template with ``{{token}}`` placeholders.
    :param data: ``.xlsx`` containing the replacement values (header row required).
    :param out_dir: Directory to write outputs into.
    :param formats: Iterable subset of ``{"docx", "xlsx", "pdf"}``. The primary
        rendered format is dictated by the template's own extension. ``"pdf"``
        triggers a post-render conversion. ``"xlsx"`` is honored only when
        the template is an .xlsx — Word→Excel conversion is not in scope.
    :param sheet: Optional sheet name within the data .xlsx.
    """
    template = Path(template)
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    kind = _detect_kind(template)
    rows = xlsx_loader.load_rows(data, sheet=sheet)
    if not rows:
        raise ValueError(f"No rows found in {data}")

    template_tokens: set[str] = (
        docx_replacer.find_tokens(template) if kind == "docx" else xlsx_replacer.find_tokens(template)
    )

    results: list[RowResult] = []
    fmt_set = {f.lower() for f in formats}

    for i, row in enumerate(rows, start=1):
        # Compose output filename.
        base = row.get("output_filename") or f"letter_{i:03d}_{_sanitize(row.get('name', ''))}"
        primary_ext = "." + kind
        primary_out = out_dir / f"{base}{primary_ext}"

        # Warn about missing data fields the template expects.
        warnings: list[str] = []
        missing = sorted(template_tokens - set(row.keys()))
        if missing:
            warnings.append(
                f"row {i}: template references {{{{ {', '.join(missing)} }}}} "
                f"but data has no such column(s)."
            )

        # Render primary output.
        if kind == "docx":
            count = docx_replacer.render(template, row, primary_out)
        else:
            count = xlsx_replacer.render(template, row, primary_out)

        result = RowResult(
            row_index=i,
            row_data=row,
            primary_out=primary_out,
            substitutions=count,
            warnings=warnings,
        )

        # PDF post-step.
        if "pdf" in fmt_set:
            pdf_out = out_dir / f"{base}.pdf"
            try:
                to_pdf(primary_out, pdf_out)
                result.pdf_out = pdf_out
            except PdfBackendUnavailable as exc:
                result.warnings.append(str(exc))

        results.append(result)
        for w in result.warnings:
            log.warning(w)

    return results
