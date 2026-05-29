# Implementation Plan

Step-by-step execution sequence. Each step has a **[State]** — `[todo]`, `[doing]`, `[done]` — and a verifiable artifact.

## Phase 1 — Scaffolding

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 1.1 | Add `requirements.txt` with `python-docx`, `openpyxl`. PDF backend (`docx2pdf` / LibreOffice) is optional at install time. | `/requirements.txt` | [done] |
| 1.2 | Create package skeleton. | `/src/doc_modifier/__init__.py`, `/src/doc_modifier/__main__.py` | [done] |

## Phase 2 — Engine

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 2.1 | Implement `xlsx_loader.load_rows(path)` returning a list of dicts. | `/src/doc_modifier/xlsx_loader.py` | [done] |
| 2.2 | Implement `docx_replacer.render(template_path, mapping, out_path)` with run-aware substitution preserving fonts and line breaks. | `/src/doc_modifier/docx_replacer.py` | [done] |
| 2.3 | Implement `xlsx_replacer.render(template_path, mapping, out_path)` for Excel-template flows (FR-6). | `/src/doc_modifier/xlsx_replacer.py` | [done] |
| 2.4 | Implement `pdf_exporter.to_pdf(src_path, out_path)` with `docx2pdf` → LibreOffice fallback. | `/src/doc_modifier/pdf_exporter.py` | [done] |
| 2.5 | Implement `pipeline.run(template, data, out_dir, formats)` orchestration. | `/src/doc_modifier/pipeline.py` | [done] |
| 2.6 | Implement CLI: `python -m doc_modifier --template … --data … --out … --formats docx,pdf`. | `/src/doc_modifier/cli.py` | [done] |

## Phase 3 — Assets

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 3.1 | Create tokenized template by replacing the 8 sample values + inline name with `{{tokens}}`. | `/templates/Template_Invitation_Letter_Adventure_India_tokenized.docx` | [done] |
| 3.2 | Create `sample_data.xlsx` with 2 example applicants. | `/data/sample_data.xlsx` | [done] |

## Phase 4 — Cowork Skill

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 4.1 | Write `SKILL.md` with trigger description, usage example, and CLI invocation. | `/.claude/skills/document-modification/SKILL.md` | [done] |

## Phase 5 — Verification

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 5.1 | Run CLI against `sample_data.xlsx`, generate 2 `.docx` + 2 `.pdf`. | `/output/` | [done] |
| 5.2 | Programmatic diff: font properties (`<w:rFonts>`, `<w:sz>`, `<w:b>`) before/after render — must be identical for replaced runs. | `/tests/test_docx_replacer.py` | [done] |
| 5.3 | Programmatic diff: count of `<w:p>` and `<w:br>` before/after — must be identical. | `/tests/test_docx_replacer.py` | [done] |
| 5.4 | Update `/docs/walkthrough.md` with results, screenshots-of-diff, file links. | `/docs/walkthrough.md` | [done] |

## Phase 6 — Documentation

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 6.1 | Refresh top-level `README.md` with usage snippet. | `/README.md` | [done] |

## Phase 7 — Slack Intake and Approval Workflow

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 7.1 | Define the Slack request payload, approval message format, and job-state schema. | `/src/doc_modifier/workflow.py`, `/src/doc_modifier/job_store.py` | [todo] |
| 7.2 | Implement Slack intake and approval routing, including pending/approve/reject transitions. | `/src/doc_modifier/slack_client.py`, `/src/doc_modifier/workflow.py` | [todo] |
| 7.3 | Add completion and rejection notifications back to Slack with request identifiers and status. | `/src/doc_modifier/slack_client.py` | [todo] |

## Phase 8 — Google Drive Delivery

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 8.1 | Implement Google Drive upload for rendered `.docx`, `.xlsx`, and `.pdf` outputs. | `/src/doc_modifier/drive_client.py` | [todo] |
| 8.2 | Persist local output paths and Drive destinations in the job record for traceability. | `/src/doc_modifier/job_store.py`, `/src/doc_modifier/workflow.py` | [todo] |
| 8.3 | Handle partial failures so local outputs are preserved when Drive upload or Slack notification fails. | `/src/doc_modifier/workflow.py`, `/src/doc_modifier/drive_client.py`, `/src/doc_modifier/slack_client.py` | [todo] |

## Phase 9 — End-to-End Verification

| # | Task | Files touched | [State] |
|---|------|---------------|---------|
| 9.1 | Simulate a Slack request followed by approval; verify one request produces the expected local files and Drive upload. | `/tests/`, `/output/` | [todo] |
| 9.2 | Verify rejection stops generation and leaves no Drive artifacts. | `/tests/` | [todo] |
| 9.3 | Verify rendering, Drive upload, and Slack notification failures are reported without deleting local outputs. | `/tests/` | [todo] |

## Traceability Matrix

| Requirement | Implemented in | Verified in |
|---|---|---|
| FR-1 | docx_replacer.py | T-1 / 5.2 |
| FR-2 | xlsx_loader.py + cli.py | T-1 |
| FR-3 | pipeline.py | T-4 / 5.1 |
| FR-4 | pdf_exporter.py + xlsx_replacer.py | T-5 / 5.1 |
| FR-5 | docx_replacer.py (`{{token}}` regex) | T-1 |
| FR-6 | xlsx_replacer.py | T-1 (xlsx path) |
| FR-7 | SKILL.md + cli.py | manual |
| FR-8 | tokenize_template.py + tokenizer frontends | T-7 |
| FR-9 | tokenize_cli.py + tokenize_template.py | T-6 |
| FR-10 | tokenize_template.py (`emit_starter_data`) | T-6 / manual |
| FR-11 | tokenize_template.py + tokenize_cli.py | T-9 |
| FR-12 | tokenize_template.py | T-8 |
| FR-13 | tokenize_cli.py + template-tokenizer Skill | manual |
| FR-14 | workflow.py + slack_client.py | T-10 / T-11 |
| FR-15 | workflow.py + slack_client.py | T-10 / T-11 |
| FR-16 | workflow.py + drive_client.py | T-11 / T-12 |
| FR-17 | slack_client.py + workflow.py | T-11 / T-12 |
| FR-18 | workflow.py + pipeline.py + tokenize_template.py | manual / template profile smoke test |
| NFR-1 | docx_replacer.py (no `<w:p>`/`<w:br>` mutation) | T-3 / 5.3 |
| NFR-2 | docx_replacer.py (preserves `<w:rPr>`) | T-2 / 5.2 |
| NFR-3 | regex confined to `{{…}}` only | T-1 |
| NFR-4 | Engine is template-agnostic; depends only on token presence | manual (apply to a 2nd template) |
| NFR-5 | pdf_exporter.py fallback chain | T-5 |
| NFR-6 | tokenize_template.py + docx_replacer.py | T-7 |
| NFR-7 | tokenize_template.py | T-7 / manual |
| NFR-8 | workflow.py + job_store.py | T-10 / T-11 / T-12 |
| NFR-9 | workflow.py + drive_client.py + slack_client.py | T-12 |
