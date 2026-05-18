"""doc_modifier — Adventure Inc. document automation engine.

Replaces ``{{placeholder}}`` tokens inside Word / Excel templates with
values supplied via an Excel data table, preserving the original
document's fonts (フォント) and line breaks (改行).

Public API:
    from doc_modifier.pipeline import run
    from doc_modifier.docx_replacer import render as render_docx
    from doc_modifier.xlsx_replacer import render as render_xlsx
"""

__version__ = "0.1.0"
