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

## 2. Non-Functional Requirements

| ID | Requirement | Source AC |
|----|-------------|-----------|
| NFR-1 | **Line breaks** (改行) of the original template **MUST NOT** be altered. | AC-1 |
| NFR-2 | **Fonts** (フォント) — family, size, bold/italic, color — **MUST NOT** be altered. | AC-2 |
| NFR-3 | Fields **NOT** listed in §FR-1 **MUST NOT** be touched. ("Avoid changing unnecessary fields") | User Story §So that |
| NFR-4 | The solution **MUST** be applicable to multiple document styles (i.e., the engine is template-agnostic; new templates need only token insertion). | AC-3 |
| NFR-5 | The CLI **MUST** run on macOS (Cowork host) without requiring Microsoft Word; PDF export falls back to LibreOffice headless if available. | Practical constraint |

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
