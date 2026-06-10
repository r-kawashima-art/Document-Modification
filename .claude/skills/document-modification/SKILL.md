---
name: document-modification
description: Use this skill whenever an administrative-department user (管理部) wants to auto-fill a Word or Excel template (e.g., 招待状 Invitation Letter, 依頼書, 申請書) from rows in an Excel data file. Trigger phrases include "招待状を作って", "テンプレートに名前を入れて", "Word テンプレートを差し込み印刷", "fill in this template from the spreadsheet", "render invitation letter from data.xlsx". Outputs preserve original fonts (フォント) and line breaks (改行); supports .docx, .xlsx, and .pdf outputs.
---

# document-modification — Adventure Inc. document automation

A reusable engine that replaces `{{placeholder}}` tokens in **Word (.docx)** or **Excel (.xlsx)** templates with values from an Excel data table. One output document is produced per row.

## Dynamic Settings Selection

**CRITICAL:** Before executing any render operation, Claude **MUST**:

1. **List available settings files** in the `settings/` directory
2. **Present the options** to the user (e.g., "sample_data.json", "project_a.json", "visa_templates.json")
3. **Ask which settings file to use** for this render task
4. **Read the chosen settings file** to determine:
   - `template_local_file`: Path to the tokenized template (`.docx` or `.xlsx`) to render from
   - `source_table_file`: Path to the data file (`.xlsx`) containing rows to fill
   - `local_output_directory`: Where to write rendered documents
   - `slack_channel_id`: Slack channel for completion notifications

This approach gives users **full control** over which project/template configuration to use on each operation, without hard-coding defaults.

**How to list and select settings:**

```bash
# Step 1: List available settings files
ls -1 settings/*.json

# Step 2: Ask user which one to use
# (e.g., "Which settings file would you like to use: sample_data.json, project_a.json, or visa_templates.json?")

# Step 3: Read the chosen settings file
python3 -c "import json; s = json.load(open('settings/YOUR_CHOSEN_FILE.json')); print(json.dumps(s, indent=2))"
```

If no settings files exist, **ask the user to create one** at `settings/your_project.json` following the template at the end of this SKILL.md.

## When to invoke this Skill

Use this skill when the user wants to:

- Generate invitation letters (招待状), visa documents (ビザ書類), or other recurring admin documents from a spreadsheet.
- Batch-render multiple copies of the same template with different field values.
- Convert the rendered output to PDF.

Do **not** use this skill for:

- Free-form drafting (use the `docx` skill instead).
- Editing the visual layout of a template (do that manually in Word).

## Inputs the user must provide or Claude must load from chosen settings

1. **A tokenized template** — a `.docx` or `.xlsx` file with placeholders of the form `{{snake_case_key}}`. Default is read from the **chosen settings file** → `template_local_file`.
2. **An Excel data file** — a `.xlsx` whose **first row is the header** (column names matching the placeholders) and each subsequent row produces one output document. Default is read from the **chosen settings file** → `source_table_file`.
3. **Output directory** — where to write rendered files. Default is read from the **chosen settings file** → `local_output_directory`.
4. **Output formats** — any subset of `docx`, `xlsx`, `pdf`. Default: `docx,pdf`.

Always confirm with the user that these settings are correct before rendering. If the user wants to override any, they can either update the settings file or specify new paths directly.

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

When preparing a data file (stored in the chosen settings file's `source_table_file`), set the `letter_date` column formula to:

```
=TEXT(TODAY(),"d mmmm, yyyy")
```

This makes every rendered letter automatically carry the current date without manual editing.

## How to run

The Skill's logic is implemented as a Python package at `src/doc_modifier/`. To execute, always **ask the user which settings file to use first**, then run:

```bash
# Step 1: Discover and ask user
ls -1 settings/*.json

# Step 2: Load chosen settings
CHOSEN_FILE="your_chosen_file.json"
TEMPLATE=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('template_local_file'))")
DATA=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('source_table_file'))")
OUTPUT=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('local_output_directory'))")

# Step 3: Render from chosen settings paths
cd /Users/r-kawashima/Projects/Document-Modification
PYTHONPATH=src python3 -m doc_modifier \
    --template "$TEMPLATE" \
    --data "$DATA" \
    --out "$OUTPUT" \
    --formats docx,pdf
```

To list the tokens a template defines (useful when onboarding a new template):

```bash
CHOSEN_FILE="your_chosen_file.json"
TEMPLATE=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('template_local_file'))")

cd /Users/r-kawashima/Projects/Document-Modification
PYTHONPATH=src python3 -m doc_modifier \
    --template "$TEMPLATE" \
    --list-tokens
```

## What Claude should do step-by-step

1. **Discover settings.** Run `ls -1 settings/*.json` to find available settings files.
2. **Ask user.** Present the list and ask which settings file they want to use for this render task.
3. **Load and confirm.** Read the chosen settings file and report:
   - Template path (`template_local_file`)
   - Data file path (`source_table_file`)
   - Output directory (`local_output_directory`)
   - Slack channel (`slack_channel_id`)
   
   Ask for confirmation before proceeding.

4. **Verify files exist.** Check that the template and data file actually exist at the paths from the chosen settings. If not, ask the user to verify the settings file or upload the files.

5. **List tokens.** Run `python3 -m doc_modifier --template <TEMPLATE_PATH> --list-tokens` using the path from the chosen settings, and compare against the data file's column headers. Surface any mismatches to the user before rendering.

6. **Infer honorifics and pronouns from the name.** When adding or updating a row for a person, derive the honorific title and pronoun columns automatically from the person's name and gender rather than asking the user to supply them manually. Use `Mr.` / he · him · his for male names and `Ms.` / she · her · her for female names. If gender cannot be determined from the name alone, ask the user. Apply the correct title as a prefix to the `name` field (e.g. `Mr. Ryosuke Kawashima`).

7. **Infer `output_filename` from the person's name.** If `output_filename` is blank or absent, derive it from the invitee's family name — e.g. `InvitationLetter_Kawashima`. Mirror the naming convention already used in the data file for consistency.

8. **Adjust style from existing rows.** When creating a new row, copy style-level fields (`letter_date`, `company`, `date_of_visit`, date formats, etc.) from the other rows already in the data file so the new document is visually consistent with the rest of the batch.

9. **Auto-fill `letter_date` when blank.** If the `letter_date` column is empty or absent for any row, populate it with today's date at prompt-execution time formatted to match the existing rows (e.g. `27 May, 2026`). Do **not** leave it blank or ask the user — just fill it in with `date.today().strftime('%-d %B, %Y')` (or equivalent) before rendering.

10. **Check pronoun columns.** If the template contains `{{pronoun_*}}` tokens, verify the data file has the required pronoun columns filled correctly (see Pronoun quick-reference above). Remind the user if any are missing.

11. **Confirm output formats.** Ask which output formats the user wants (`docx`, `xlsx`, `pdf`). Default to `docx,pdf` unless specified otherwise.

12. **Run the pipeline.** Use the environment-variable-based bash command above with the user's chosen `--formats`, reading all paths from the **chosen settings file**.

13. **Send Slack notification.** Immediately after the pipeline finishes, run:

    ```bash
    cd /Users/r-kawashima/Projects/Document-Modification
    SLACK_CHANNEL=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('slack_channel_id'))")
    python3 -c "
    import sys; sys.path.insert(0, 'src')
    from slack_notifier import notify_completion
    notify_completion('$SLACK_CHANNEL', '<OUTPUT_DIR>', '<NUM_DOCS>')
    "
    ```

    If the command fails (e.g. missing Slack token), report the error to the user but do **not** treat it as a pipeline failure — the documents were already generated successfully.

14. **Present outputs.** Surface the rendered files in the output directory (from the chosen settings) via `computer://` links. Never silently overwrite a non-empty output directory — append a timestamp if collisions are likely.

15. **Confirm preservation.** Mention to the user that fonts and line breaks are preserved by design (Acceptance Criteria #1 and #2 from `specs/user_story.md`).

16. **Report statistics.** Print the substitution count per row (e.g. "14 substitutions per row, 3 documents rendered").

## Onboarding a new template

To add support for, say, an Adventure China invitation letter:

1. Take the original `.docx` and replace each editable value with a `{{snake_case_token}}`.
2. **Create a new settings file** (e.g., `settings/china_visas.json`) with paths pointing to:
   - Your new template (e.g., `templates/template_china_letter.docx`)
   - A data file (e.g., `data/china_applicants.xlsx`)
   - An output directory (e.g., `output/china_letters`)
3. Add matching column headers to the data `.xlsx` file.
4. When the user wants to render, they'll select `settings/china_visas.json` from the list.

## Acceptance guarantees

- **Fonts** (`<w:rFonts>`, `<w:sz>`, `<w:b>`, `<w:color>`) of replaced runs are preserved bit-for-bit.
- **Line breaks** (`<w:p>`, `<w:br>`) are never inserted or removed.
- Fields **not** marked with a `{{token}}` are never touched.
- **User choice is respected**: Claude always asks which settings file to use, never assumes a default.

## Settings File Template

If the user needs to create a new settings file (e.g., `settings/visa_templates.json`), use this template:

```json
{
    "template_local_file": "templates/template_visa_letter.docx",
    "source_table_file": "data/visa_applicants.xlsx",
    "local_output_directory": "output/visa_letters",
    "output_Google_drive_directory": "https://drive.google.com/drive/folders/YOUR_FOLDER_ID",
    "data_source_spreadsheet": "https://docs.google.com/spreadsheets/d/YOUR_SHEET_ID/edit",
    "slack_channel_id": "C0B6Z2AHUTB"
}
```

Settings files are stored in `settings/` and can be named anything (e.g., `project_a.json`, `client_xyz.json`, `visa_batch_2026.json`). Each file represents a different template project with its own paths.
