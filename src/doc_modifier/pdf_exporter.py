"""Convert rendered ``.docx`` / ``.xlsx`` files to ``.pdf``.

Backend chain (tried in order):
    1. ``docx2pdf`` — uses Microsoft Word's automation API on macOS/Windows.
    2. LibreOffice headless — ``soffice --headless --convert-to pdf``.

If neither is available, raises :class:`PdfBackendUnavailable` with an
actionable hint.
"""
from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class PdfBackendUnavailable(RuntimeError):
    """No PDF conversion backend (Word / LibreOffice) found on this host."""


def _try_docx2pdf(src: Path, out: Path) -> bool:
    try:
        from docx2pdf import convert  # type: ignore
    except Exception:
        return False
    try:
        convert(str(src), str(out))
        return out.exists()
    except Exception:
        return False


def _try_libreoffice(src: Path, out: Path) -> bool:
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        return False
    out.parent.mkdir(parents=True, exist_ok=True)
    try:
        result = subprocess.run(
            [
                soffice,
                "--headless",
                "--convert-to",
                "pdf",
                "--outdir",
                str(out.parent),
                str(src),
            ],
            capture_output=True,
            timeout=120,
        )
        produced = out.parent / (src.stem + ".pdf")
        if produced.exists():
            if produced != out:
                produced.replace(out)
            return True
        return False
    except subprocess.TimeoutExpired:
        return False


def to_pdf(src_path: str | Path, out_path: str | Path) -> Path:
    """Convert ``src_path`` (a .docx or .xlsx) to PDF at ``out_path``.

    Raises :class:`PdfBackendUnavailable` if no backend succeeds.
    """
    src = Path(src_path)
    out = Path(out_path)

    if _try_docx2pdf(src, out):
        return out
    if _try_libreoffice(src, out):
        return out

    raise PdfBackendUnavailable(
        "Could not export PDF. Install either Microsoft Word "
        "(then `pip install docx2pdf`) or LibreOffice "
        "(`brew install --cask libreoffice` on macOS)."
    )
