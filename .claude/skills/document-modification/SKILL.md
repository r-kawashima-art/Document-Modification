---
name: document-modification
description: Use this skill whenever an administrative-department user (管理部) wants to auto-fill a Word or Excel template (e.g., 招待状 Invitation Letter, 依頼書, 申請書) from rows in an Excel data file. Trigger phrases include "招待状を作って", "テンプレートに名前を入れて", "Word テンプレートを差し込み印刷", "fill in this template from the spreadsheet", "render invitation letter from data.xlsx". Outputs preserve original fonts (フォント) and line breaks (改行); supports .docx, .xlsx, and .pdf outputs.
---

# document-modification — Adventure Inc. document automation

A reusable engine that replaces `{{placeholder}}` tokens in **Word (.docx)** or **Excel (.xlsx)** templates with values from an Excel data table. One output document is produced per row.

## When to invoke this Skill

Use this skill when the user wants to:

- Generate invitation letters (招待状), visa documents (ビザ書類), or other recurring admin documents from a spreadsheet.
- Batch-render multiple copies of the same template with different field values.
- Convert the rendered output to PDF.

Do **not** use this skill for:

- Free-form drafting (use the `docx` skill instead).
- Editing the visual layout of a template (do that manually in Word).

## Inputs the user must provide

1. **A tokenized template** — a `.docx` or `.xlsx` file with placeholders of the form `{{snake_case_key}}` where values should land. The default Adventure invitation-letter template lives at `templates/Template_Invitation_Letter_Adventure_India_tokenized.docx`.
2. **An Excel data file** — a `.xlsx` whose **first row is the header** (column names matching the placeholders) and each subsequent row produces one output document.
3. **Output formats** — any subset of `docx`, `xlsx`, `pdf`.

If the user only mentions one of these, ask for the rest.

## Default schema for the Invitation Letter

| Column header | Token in template | Notes |
|---|---|---|
| `letter_date` | `{{letter_date}}` | Date printed at the top of the letter (e.g. `26th May, 2026`). To auto-fill today's date, populate this column with `=TEXT(TODAY(),"d mmmm, yyyy")` in Excel, or pass the formatted date string directly. |
| `name` | `{{name}}` | Full name including title (e.g. `Mr. Taro Yamada`) |
| `date_of_birth` | `{{date_of_birth}}` | |
| `nationality` | `{{nationality}}` | |
| `passport_no` | `{{passport_no}}` | |
| `passport_issuing_country` | `{{passport_issuing_country}}` | |
| `date_of_issue` | `{{date_of_issue}}` | |
| `date_of_expiry` | `{{date_of_expiry}}` | |
| `mobile_no` | `{{mobile_no}}` | |
| `company` | `{{company}}` | Company the invitee belongs to (e.g. `Adventure, Inc.`) |
| `date_of_visit` | `{{date_of_visit}}` | Intended visit date (e.g. `26th May, 2026`) |
| `pronoun_subj` | `{{pronoun_subj}}` | Subject pronoun — `he` or `she` |
| `pronoun_subj_cap` | `{{pronoun_subj_cap}}` | Capitalised subject pronoun — `He` or `She` |
| `pronoun_obj` | `{{pronoun_obj}}` | Object pronoun — `him` or `her` |
| `pronoun_poss` | `{{pronoun_poss}}` | Possessive pronoun — `his` or `her` |
| `output_filename` *(optional)* | — | Used as the output basename |

### Pronoun quick-reference

| Gender | `pronoun_subj` | `pronoun_subj_cap` | `pronoun_obj` | `pronoun_poss` |
|---|---|---|---|---|
| Male | `he` | `He` | `him` | `his` |
| Female | `she` | `She` | `her` | `her` |

### Auto-filling `letter_date` with today's date

When preparing `data/sample_data.xlsx`, set the `letter_date` column formula to:

```
=TEXT(TODAY(),"d mmmm, yyyy")
```

This makes every rendered letter automatically carry the current date without manual editing.

## How to run

The Skill's logic is implemented as a Python package at `src/doc_modifier/`. To execute:

```bash
cd /Users/r-kawashima/Projects/Document-Modification
PYTHONPATH=src python3 -m doc_modifier \
    --template templates/Template_Invitation_Letter_Adventure_India_tokenized.docx \
    --data data/sample_data.xlsx \
    --out output/ \
    --formats docx,pdf
```

To list the tokens a template defines (useful when onboarding a new template):

```bash
PYTHONPATH=src python3 -m doc_modifier \
    --template path/to/some_template.docx \
    --list-tokens
```

## What Claude should do step-by-step

1. **Confirm inputs.** Ask the user for the template path and the data .xlsx path if not already given. Verify both files exist.
2. **List tokens.** Run `python3 -m doc_modifier --template <path> --list-tokens` and compare against the data file's column headers. Surface any mismatches to the user before rendering.
3. **Infer honorifics and pronouns from the name.** When adding or updating a row for a person, derive the honorific title and pronoun columns automatically from the person's name and gender rather than asking the user to supply them manually. Use `Mr.` / he · him · his for male names and `Ms.` / she · her · her for female names. If gender cannot be determined from the name alone, ask the user. Apply the correct title as a prefix to the `name` field (e.g. `Mr. Ryosuke Kawashima`).
4. **Infer `output_filename` from the person's name.** If `output_filename` is blank or absent, derive it from the invitee's family name — e.g. `InvitationLetter_Kawashima`. Mirror the naming convention already used in the data file for consistency.
5. **Adjust style from existing rows.** When creating a new row, copy style-level fields (`letter_date`, `company`, `date_of_visit`, date formats, etc.) from the other rows already in the data file so the new document is visually consistent with the rest of the batch.
6. **Auto-fill `letter_date` when blank.** If the `letter_date` column is empty or absent for any row, populate it with today's date at prompt-execution time formatted to match the existing rows (e.g. `27 May, 2026`). Do **not** leave it blank or ask the user — just fill it in with `date.today().strftime('%-d %B, %Y')` (or equivalent) before rendering.
7. **Check pronoun columns.** If the template contains `{{pronoun_*}}` tokens, verify the data file has the required pronoun columns filled correctly (see Pronoun quick-reference above). Remind the user if any are missing.
8. **Run the pipeline.** Use the bash command above with the user's chosen `--formats`.
9. **Send Slack notification.** Immediately after the pipeline finishes, run:

   ```bash
   cd /Users/r-kawashima/Projects/Document-Modification
   python3 src/slack_notifier.py
   ```

   This posts a completion summary to the configured Slack channel. If the command fails (e.g. missing `SLACK_BOT_TOKEN` in `.env`), report the error to the user but do **not** treat it as a pipeline failure — the documents were already generated successfully.

10. **Present outputs.** Surface the rendered files in `output/` via computer:// links. Never silently overwrite a non-empty `output/` directory — append a timestamp if collisions are likely.
11. **Confirm preservation.** Mention to the user that fonts and line breaks are preserved by design (Acceptance Criteria #1 and #2 from `specs/user_story.md`).

## Onboarding a new template

To add support for, say, an Adventure China invitation letter:

1. Take the original `.docx` and replace each editable value with a `{{snake_case_token}}`.
2. Save under `templates/`.
3. Add matching column headers to the user's Excel data file.
4. Re-run the CLI — no engine change is required (NFR-4: template-agnostic).

## Acceptance guarantees

- **Fonts** (`<w:rFonts>`, `<w:sz>`, `<w:b>`, `<w:color>`) of replaced runs are preserved bit-for-bit.
- **Line breaks** (`<w:p>`, `<w:br>`) are never inserted or removed.
- Fields **not** marked with a `{{token}}` are never touched.
