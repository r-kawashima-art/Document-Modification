# Requirements

Derived from `user_story.md`. The "Why" → "What" → measurable "Done".

## 1. Functional Requirements

| ID | Requirement | Source AC |
|----|-------------|-----------|
| FR-1 | The system **MUST** replace the 8 designated fields (Name, Date of birth, Nationality, Passport No., Passport issuing country, Date of Issue, Date of Expiry, Mobile No.) inside a Word template. | User Story §Required fields |
| FR-2 | The system **MUST** accept a Word template (.docx) and an Excel table (.xlsx) as the two canonical inputs. | Cowork answer: "Word Docs and Excel Tables" |
| FR-3 | The system **MUST** generate one output document per row in the Excel table. | Implied by batch use case (e.g., multiple visa applicants) |
| FR-4 | The system **MUST** support output as **.docx**, **.xlsx**, and **.pdf**. | Cowork answer: ".docx + .xlsx + .pdf" |
| FR-5 | Fields **MUST** be marked using placeholder tokens of the form `{{snake_case_key}}`. | Cowork answer: "Placeholder tokens" |
| FR-6 | The engine **MUST** also work on `.xlsx` templates (placeholder tokens inside cells), enabling reuse for non-Word admin documents. | AC-3: "applicable to multiple styles" |
| FR-7 | The system **MUST** be invokable both as a **Cowork Skill** and as a **standalone CLI** (Command Line Interface). | Cowork answer: "Both Skill + CLI" |
| FR-8 | The system **MUST** auto-tokenize a source `.docx` by detecting label:value tables and generating `snake_case` placeholder tokens, producing a tokenized template that the renderer (FR-1…FR-4) can consume directly. | Cowork follow-up: "automate creation of tokenized documents" |
| FR-9 | The tokenizer **MUST** support a two-step **preview → apply** workflow: `--dry-run` prints the proposed plan without writing; the apply step writes only after explicit invocation. | UX safety; supports NFR-3 |
| FR-10 | The tokenizer **MUST** be able to emit a starter `.xlsx` data file whose header row matches the generated tokens and whose first data row is pre-filled with the source's original sample values. | Onboarding speed; pairs with FR-2 |
| FR-11 | The tokenizer **MUST** accept an explicit override mapping (`.yaml` / `.json` / `.xlsx`) that supplements — or, with `--no-auto-detect`, replaces — the auto-detected plan. | Cover inline-only fields the heuristic misses |
| FR-12 | The tokenizer **MUST** distinguish *cell-scoped* replacements (one specific table cell) from *document-wide* replacements (e.g. inline body matches), so two table rows sharing the same sample value (e.g. "Japan") can receive distinct tokens without bleed-over. | Ambiguity correctness; surfaced during smoke test |
| FR-13 | The tokenizer **MUST** be invokable both as a **Cowork Skill** (`template-tokenizer`) and as a **standalone CLI** (`python -m doc_modifier.tokenize_cli`). | Same dual-front-end principle as FR-7 |

## 2. Non-Functional Requirements

| ID | Requirement | Source AC |
|----|-------------|-----------|
| NFR-1 | **Line breaks** (改行) of the original template **MUST NOT** be altered. | AC-1 |
| NFR-2 | **Fonts** (フォント) — family, size, bold/italic, color — **MUST NOT** be altered. | AC-2 |
| NFR-3 | Fields **NOT** listed in §FR-1 **MUST NOT** be touched. ("Avoid changing unnecessary fields") | User Story §So that |
| NFR-4 | The solution **MUST** be applicable to multiple document styles (i.e., the engine is template-agnostic; new templates need only token insertion). | AC-3 |
| NFR-5 | The CLI **MUST** run on macOS (Cowork host) without requiring Microsoft Word; PDF export falls back to LibreOffice headless if available. | Practical constraint |
| NFR-6 | The tokenizer **MUST** preserve fonts (フォント) and line breaks (改行) of the source document — same guarantee the renderer provides (NFR-1, NFR-2). The tokenized output must be byte-equivalent in `<w:p>` / `<w:br>` counts to the source. | AC-1 / AC-2 extended to tokenization |
| NFR-7 | The tokenizer **MUST NOT** modify the source file in place. Source documents live in `templates/originals/`; tokenized outputs are written to `templates/<new_name>.docx`. | Data-loss prevention |

## 3. Out of Scope

- OCR (Optical Character Recognition, 光学文字認識) of scanned PDFs.
- Auto-detecting fields without placeholder tokens (rejected in favor of explicit `{{token}}` marking).
- Editing or signing PDFs after generation.
- Sending the generated document by email/Slack (handled by a separate downstream automation).

## 4. Acceptance Test Matrix

| Test | Method | Pass criterion |
|------|--------|----------------|
| T-1 | Render `Template_Invitation_Letter_…_tokenized.docx` against `sample_data.xlsx` row 1. | Output `.docx` contains row-1 values in all 8 fields; no other text changed. |
| T-2 | Byte-compare the original `<w:rFonts>` and `<w:rPr>` elements before and after rendering for each replaced run. | Font properties are identical. |
| T-3 | Count `<w:br>` and `<w:p>` elements before and after rendering. | Counts are identical → AC-1 satisfied. |
| T-4 | Render the template with an `.xlsx` data source containing 2 rows; verify 2 output `.docx` files. | Batch mode works. |
| T-5 | Generate `.pdf` from the rendered `.docx`. | PDF opens, contains substituted values. |
| T-6 | Run `tokenize_cli --source originals/Source.docx --dry-run`. | No file is written; the proposed plan is printed with token, label, original value, and location for each replacement. |
| T-7 | Tokenize the original Adventure India invitation letter, render against `sample_data.xlsx`, then compare to the hand-built tokenized template's render. | Rendered text is byte-equal; `<w:p>` and `<w:br>` counts identical at source / auto-tokenized / rendered stages (53 / 53 / 53 and 0 / 0 / 0). |
| T-8 | Two table rows both containing the value "Japan" are present in the source. | Tokenizer assigns distinct tokens (`{{nationality}}` and `{{passport_issuing_country}}`) cell-scoped; ambiguity warning is printed; no doc-wide bleed-over. |
| T-9 | Provide `--mapping mappings.yaml` with one entry not present in any table. | The entry is honored as a doc-wide replacement; auto-detect plan still runs (unless `--no-auto-detect` was passed). |
