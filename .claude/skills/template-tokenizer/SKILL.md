---
name: template-tokenizer
description: Use this skill whenever the user wants to CONVERT an existing Word (.docx) or Excel (.xlsx) document into a reusable tokenized template with {{snake_case}} placeholders, instead of editing it manually in Word. Trigger phrases include "テンプレ化して", "tokenize this document", "make a template from this file", "auto-detect the fields in this Word doc", "turn this invitation letter into a reusable template". Pair this skill with the document-modification skill: this one creates the template, that one fills it.
---

# template-tokenizer — Auto-create a tokenized template from any document

This skill removes the manual find-and-replace step from template onboarding (README §5). Given a source `.docx` with a label : value table, it:

1. **Discover available settings files** from the `settings/` directory.
2. **Ask the user which settings to use** for this tokenization task.
3. Auto-detects fields.
4. Generates `snake_case` token names from each label.
5. Sweeps the body for inline duplicates of table values.
6. Emits a tokenized `.docx` **plus** a starter `.xlsx` data file with the right header row and one example row pre-filled.

The engine preserves fonts (フォント) and line breaks (改行) bit-for-bit — same run-aware logic the `document-modification` skill uses at render time.

## Dynamic Settings Selection

**CRITICAL:** Before executing any tokenization, Claude **MUST**:

1. **List available settings files** in the `settings/` directory
2. **Present the options** to the user (e.g., "sample_data.json", "project_a.json", "visa_templates.json")
3. **Ask which settings file to use** for this task
4. **Read the chosen settings file** to determine:
   - `template_local_file`: Template output path (where to save the tokenized `.docx`)
   - `source_table_file`: Default data file path (where to save the starter `.xlsx`)
   - `local_output_directory`: Where to write all output files
   - `slack_channel_id`: Slack channel for notifications after tokenization completes

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

- The user uploaded or referenced an admin document (招待状, 依頼書, 申請書, contract, etc.) and wants to "make a template" out of it.
- The user mentions «テンプレ化», "tokenize", "extract fields", "create a template from".
- Onboarding a brand-new document type into the document-modification pipeline.
- The user wants to **add new tokens** to an already-tokenized template (use `--mapping` + `--no-auto-detect`).

Do **not** use this skill for:

- Rendering filled-in documents from an existing template — use `document-modification` instead.
- Free-form drafting from scratch — use `docx` instead.

## Two-step workflow

Always follow this two-step workflow so the user reviews what the tokenizer proposes before any file is written.

### Step 0. Discover and Select Settings

```bash
# List available settings files
ls -1 settings/*.json 2>/dev/null
```

Present the list to the user:
> "I found these settings files: **sample_data.json**, **project_a.json**, **visa_templates.json**. Which one would you like to use for this tokenization?"

Once the user selects, read the chosen file:

```bash
python3 -c "import json; s = json.load(open('settings/CHOSEN_FILE.json')); \
  print('Template output:', s.get('template_local_file')); \
  print('Starter data:', s.get('source_table_file')); \
  print('Output dir:', s.get('local_output_directory')); \
  print('Slack channel:', s.get('slack_channel_id'))"
```

**Report these paths back to the user** and confirm they're correct before proceeding to Step 1.

### Step 1. Dry-run / analyze

```bash
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "<path/to/source.docx>" \
    --dry-run
```

Read the output back to the user as a table of proposed tokens. Surface:

- Any warning about ambiguous values (same text → multiple candidate tokens). The tokenizer keeps those cell-scoped automatically, but the user may want to rename one of them.
- Any "skipped" tables that don't match the label:value pattern (the user may want to add them via an explicit mapping file).

Then ask the user:

> Does this look right? Should I rename any tokens, or add fields the auto-detector missed?

### Step 2. Apply

Once the user confirms (or supplies overrides), read the chosen settings again, then run:

```bash
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "<path/to/source.docx>" \
    --out "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('template_local_file'))")" \
    --starter-data "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('source_table_file'))")"
```

This ensures the output paths respect the user's **chosen** settings file, not a default.

## Supplying explicit overrides

If the auto-detect mode misses fields or names them poorly, the user can supply an explicit mapping in YAML, JSON, or .xlsx:

```yaml
# mappings.yaml — keys are the original text, values are the token name (no {{ }})
"Mr. Takamichi Yanai": name
"+81 90-8501-0521":    mobile_no
"Adventure India Journey Private Limited": signing_entity
```

Then:

```bash
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source source.docx \
    --mapping mappings.yaml \
    --out "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('template_local_file'))")" \
    --starter-data "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('source_table_file'))")"
```

The mapping is merged with auto-detect (mapping wins on conflicts).

## Adding tokens to an already-tokenized template

When the user wants to add new `{{tokens}}` to a template that already has existing placeholders (e.g. adding `letter_date`, `company`, pronoun tokens), use `--no-auto-detect` so the engine only applies the explicit mapping without trying to re-tokenize existing `{{...}}` strings:

```bash
# 1. Dry-run to preview
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('template_local_file'))")" \
    --mapping data/new_tokens.yaml \
    --no-auto-detect \
    --dry-run -v

# 2. Apply (overwrites the template in-place; engine preserves all existing tokens)
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('template_local_file'))")" \
    --mapping data/new_tokens.yaml \
    --no-auto-detect \
    --out "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('template_local_file'))")" \
    --starter-data "$(python3 -c "import json; print(json.load(open('settings/YOUR_CHOSEN_FILE.json')).get('source_table_file'))")"
```

> **Longest-match safety**: the engine sorts doc-wide replacements by descending length before applying them. This means longer strings like `"his/her"` are replaced before shorter substrings like `"her"`, preventing double-replacements. Rely on this when mapping pronoun variants.

## Standard token set for the Adventure India Invitation Letter

The tokenized template (path determined by the **chosen settings file**) uses these tokens:

| Token | Typical value | Source in original doc |
|---|---|---|
| `{{letter_date}}` | `26th May, 2026` | Date at top of letter |
| `{{name}}` | `Mr. Taro Yamada` | Name field in table + body |
| `{{date_of_birth}}` | `01/01/1990` | Table |
| `{{nationality}}` | `Japan` | Table |
| `{{passport_no}}` | `AB1234567` | Table |
| `{{passport_issuing_country}}` | `Japan` | Table |
| `{{date_of_issue}}` | `01/01/2020` | Table |
| `{{date_of_expiry}}` | `01/01/2030` | Table |
| `{{mobile_no}}` | `+81 90-0000-0000` | Table |
| `{{company}}` | `Adventure, Inc.` | Body paragraph |
| `{{date_of_visit}}` | `26th May, 2026` | Body paragraph |
| `{{pronoun_subj}}` | `he` / `she` | Body paragraph (lowercase subject) |
| `{{pronoun_subj_cap}}` | `He` / `She` | Body paragraph (capitalised subject) |
| `{{pronoun_obj}}` | `him` / `her` | Body paragraph (object) |
| `{{pronoun_poss}}` | `his` / `her` | Body paragraph (possessive) |

### Pronoun mapping by gender

| Gender | `pronoun_subj` | `pronoun_subj_cap` | `pronoun_obj` | `pronoun_poss` |
|---|---|---|---|---|
| Male | `he` | `He` | `him` | `his` |
| Female | `she` | `She` | `her` | `her` |

## What Claude should do step-by-step

1. **Discover settings.** Run `ls -1 settings/*.json` to find available settings files.
2. **Ask user.** Present the list and ask which settings file they want to use for this tokenization.
3. **Load and confirm.** Read the chosen settings file and report the template output path, starter data path, and output directory. Ask for confirmation.
4. **Locate the source.** Confirm the source `.docx` path with the user. If the user uploaded a file, copy it under `templates/originals/` (don't tokenize in place — always preserve the original).
5. **Dry-run.** Run the CLI with `--dry-run` and read the proposed plan back to the user as a table (token, original value, location).
6. **Handle ambiguity.** If the tokenizer reports an ambiguous value (e.g. "Japan" → two tokens), confirm with the user that the cell-scoped treatment is acceptable, or offer to add an explicit mapping.
7. **Confirm.** Ask the user to approve the plan. **Use the paths from the chosen settings file**.
8. **Apply.** Run the CLI again without `--dry-run`, passing `--out` and `--starter-data` using values from the chosen settings file.
9. **Verify.** The CLI prints "Tokens present in output (N): …". Read those tokens back to the user and confirm they match the starter data file's header row.
10. **Slack notification.** After successful tokenization, post a notification to the `slack_channel_id` from the chosen settings file (if configured).
11. **Hand off.** Suggest the user can now invoke the `document-modification` skill to render letters from the starter data file (or their own).

## Quality bar

- Never tokenize the user's only copy of the source document — always write to a new path.
- Never modify the source's fonts or line breaks. The engine guarantees this; double-check by counting `<w:p>` and `<w:br>` if the user is worried.
- If `--dry-run` produces zero replacements, the source has no label:value table the heuristic recognizes. Suggest the explicit-mapping mode (YAML/JSON/xlsx).
- **Always ask the user which settings file to use.** Do not assume or pick one automatically.
- **Always validate the chosen settings file** exists and contains required keys before proceeding. If incomplete, ask the user to update it.

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
