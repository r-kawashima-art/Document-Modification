---
name: doc-automation-runner
description: Use this skill whenever an Adventure Inc. teammate wants Claude to RUN a Python script in this repository on their behalf — tokenize a Word doc, render letters from a spreadsheet, convert a .docx to PDF, list a template's tokens, inspect a data file's columns, install dependencies, or run the test suite. This skill is the single front door for every Python entry point under src/doc_modifier/. Trigger phrases include "run the document automation", "run the python script", "do this for me with the engine", "automate this with the doc tools", "process these documents", "Pythonでやって", "実行して", "テンプレ化と差し込み両方やって". For pure tokenize-only or pure render-only requests, this skill DELEGATES to the task-specific skills (template-tokenizer / document-modification) rather than bypassing them.
---

# doc-automation-runner — single entry point for every Python script

Adventure Inc.'s administrative department (管理部) does not need to memorize which CLI does what. This skill maps any high-level request to the correct underlying Python entry point, runs it, and presents the results — without asking the user to learn `python -m doc_modifier.tokenize_cli` syntax.

**Key principle:** All file paths and configuration are determined by **user choice** — Claude always lists available settings files and asks which one to use before executing any operation.

## Dynamic Settings Selection

Before any CLI invocation, Claude **MUST**:

1. **List available settings files** in the `settings/` directory
2. **Present the options** to the user
3. **Ask which settings file to use** for this operation
4. **Read the chosen settings file** to load configuration

This ensures users maintain **full control** over which project/template setup is active, with no hard-coded defaults.

**How to list and select settings:**

```bash
# Step 1: List available settings files
ls -1 settings/*.json

# Step 2: Ask user which one to use
# (e.g., "Which settings file would you like to use for this operation?")

# Step 3: Read the chosen settings file
python3 -c "import json; s = json.load(open('settings/YOUR_CHOSEN_FILE.json')); print(json.dumps(s, indent=2))"
```

## When to invoke this Skill

Invoke `doc-automation-runner` when **any** of the following are true:

- The user wants Claude to run code from this repository.
- The user describes a multi-step workflow that touches more than one script (e.g. "tokenize this AND fill it from data AND give me PDFs").
- The user wants a utility operation that has no dedicated Skill: PDF-only conversion, token inspection, test run, dependency install, data-file inspection.
- The user is unsure which tool they need — let this skill classify intent.

Do **not** invoke this Skill when the user has already named one of the task-specific skills explicitly ("use the tokenizer", "use the renderer"). In that case, invoke that skill directly (which will handle settings selection internally).

## Intent → Action routing

Classify the user's request against this table **first**.

| Intent (利用者の意図) | Trigger phrases | Action |
|---|---|---|
| Tokenize a source document | "make a template", "テンプレ化", "tokenize this Word doc" | **Delegate** to the `template-tokenizer` Skill (which will ask user to choose settings). |
| Fill a template from data | "render letters", "招待状作って", "fill the template" | **Delegate** to the `document-modification` Skill (which will ask user to choose settings). |
| Tokenize then render in one chain | "from this raw doc, produce filled PDFs", "テンプレ化してから差し込みも" | Chain both delegations in sequence. Each will independently ask user to choose settings. |
| List tokens in a template | "what tokens does this template have?", "list the placeholders" | Ask user which settings file to use, then run `python -m doc_modifier --template <TEMPLATE_FROM_CHOSEN_SETTINGS> --list-tokens`. |
| Inspect columns in a data .xlsx | "what columns are in this spreadsheet?", "show me the data headers" | Ask user which settings file to use, then run openpyxl inspector using `source_table_file` from chosen settings. |
| Convert a .docx (or .xlsx) to PDF only | "convert this docx to pdf", "pdf化して" | Ask user which settings file to use, then run one-liner calling `doc_modifier.pdf_exporter.to_pdf()` on the template from chosen settings. |
| Install / set up the project | "install dependencies", "set this up on my Mac" | Run `pip install -r requirements.txt`; suggest LibreOffice fallback for PDF. (No settings file needed.) |
| Run the acceptance tests | "verify the engine", "run the tests", "check fonts and line breaks still survive" | Run `python3 tests/test_docx_replacer.py`. (No settings file needed.) |
| Dry-run / preview anything | "preview only", "don't write yet", "--dry-run" | Ask user which settings file to use, then forward the `--dry-run` flag to whichever underlying CLI applies. |

If a user request maps to more than one row, ask one clarifying question rather than guessing.

## Catalog of Python entry points

Read this once before suggesting commands; route everything through these entry points. **For operations requiring file paths, always ask user to choose settings first.**

| Module / script | Direct CLI invocation | What it does |
|---|---|---|
| `doc_modifier.cli` | `PYTHONPATH=src python -m doc_modifier --template [from chosen settings] --data [from chosen settings] --out [from chosen settings] --formats docx,pdf` | Renderer entry. Fills a tokenized template with rows from a data .xlsx. |
| `doc_modifier.cli` (inspect mode) | `PYTHONPATH=src python -m doc_modifier --template [from chosen settings] --list-tokens` | Print every `{{token}}` referenced by a template. |
| `doc_modifier.tokenize_cli` | `PYTHONPATH=src python -m doc_modifier.tokenize_cli --source … --out [from chosen settings] --starter-data [from chosen settings]` | Tokenizer entry. Converts a source `.docx` into a tokenized template + optional starter data file. |
| `doc_modifier.tokenize_cli` (preview mode) | `PYTHONPATH=src python -m doc_modifier.tokenize_cli --source … --dry-run` | Print the proposed tokenization plan without writing anything. |
| `doc_modifier.pipeline` | (library only) | Orchestration used by `doc_modifier.cli`. Not invoked directly. |
| `doc_modifier.tokenize_template` | (library only) | Tokenizer engine. Not invoked directly. |
| `doc_modifier.docx_replacer` | (library only) | Run-aware `.docx` text replacement. Not invoked directly. |
| `doc_modifier.xlsx_replacer` | (library only) | Cell-level `.xlsx` token replacement. |
| `doc_modifier.xlsx_loader` | (library only) | Row loader for data files. Header normalization. |
| `doc_modifier.pdf_exporter` | `python -c "from doc_modifier.pdf_exporter import to_pdf; to_pdf('[template from chosen settings]', '<out.pdf>')"` | docx2pdf → LibreOffice fallback. |
| `tests/test_docx_replacer.py` | `python3 tests/test_docx_replacer.py` | Framework-free acceptance tests. |

All commands assume `cd /Users/r-kawashima/Projects/Document-Modification` and `PYTHONPATH=src` are set.

## Cookbook of common operations

Use this when the user request matches one of the rows below. **Always ask the user which settings file to use first (except for install/tests, which don't need settings).** Run the listed bash command; **do not invent new flags**.

### 0. Discover and Select Settings (for most operations)

```bash
cd /Users/r-kawashima/Projects/Document-Modification

# List available settings files
ls -1 settings/*.json

# Ask user: "Which settings file would you like to use?"
# (user responds with filename, e.g., "sample_data.json")
```

Report the list and capture the user's choice.

### 1. List the tokens a template defines

```bash
cd /Users/r-kawashima/Projects/Document-Modification
CHOSEN_FILE="user_selected_file.json"
TEMPLATE=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('template_local_file'))")
PYTHONPATH=src python3 -m doc_modifier --template "$TEMPLATE" --list-tokens
```

Read the printed list back to the user. If they are about to render, compare it to the data file's columns and surface any mismatch.

### 2. Show the columns in a data .xlsx

```bash
cd /Users/r-kawashima/Projects/Document-Modification
CHOSEN_FILE="user_selected_file.json"
DATA=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('source_table_file'))")
python3 -c "
from openpyxl import load_workbook
wb = load_workbook('$DATA', data_only=True)
ws = wb.active
print('Sheet:', ws.title)
print('Columns:', [c.value for c in next(ws.iter_rows(max_row=1))])
print('Rows:', ws.max_row - 1)
"
```

### 3. Convert an existing `.docx` to `.pdf` (no rendering, no tokenizing)

```bash
cd /Users/r-kawashima/Projects/Document-Modification
CHOSEN_FILE="user_selected_file.json"
TEMPLATE=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('template_local_file'))")
PYTHONPATH=src python3 -c "
from doc_modifier.pdf_exporter import to_pdf
to_pdf('$TEMPLATE', '${TEMPLATE%.docx}.pdf')
print('PDF written.')
"
```

If `PdfBackendUnavailable` is raised, suggest `brew install --cask libreoffice` (macOS) and re-run.

### 4. Install or refresh dependencies

```bash
cd /Users/r-kawashima/Projects/Document-Modification && pip install -r requirements.txt
```

If the user wants PDF support and doesn't have Microsoft Word, also suggest:
```bash
brew install --cask libreoffice
```

**Note:** This operation does NOT require choosing a settings file.

### 5. Verify the engine (run acceptance tests)

```bash
cd /Users/r-kawashima/Projects/Document-Modification && python3 tests/test_docx_replacer.py
```

Read the `✓` lines back to the user — if any fail, do not proceed with rendering work until investigated.

**Note:** This operation does NOT require choosing a settings file.

### 6. End-to-end chain: source `.docx` → tokenized template → filled PDFs

For chained workflows, **delegate to both Skills in sequence**. Each will independently ask the user which settings file to use:

**In Cowork chat:**
> *"From `templates/originals/<Source.docx>`, make a template and render filled PDFs."*

Claude will:
1. Delegate to `template-tokenizer` Skill
   - Template-tokenizer asks user to choose settings file
   - Tokenizer reads chosen settings and outputs template
2. Delegate to `document-modification` Skill
   - Document-modification asks user to choose settings file (may be same or different)
   - Renderer reads chosen settings and outputs filled documents

This skill (`doc-automation-runner`) orchestrates the sequence but **does NOT** pick settings itself — each delegated Skill asks the user.

## Standard operating procedure

1. **Classify intent.** Match the user's words to one row of "Intent → Action routing".
2. **Delegate if appropriate.** For pure tokenize/render/chain requests, hand off to the task-specific Skills (which will ask user to choose settings).
3. **Ask for settings (if not delegating).** For utility operations, ask user which settings file to use. List options from `ls -1 settings/*.json`.
4. **Load and confirm.** Read the chosen settings file and report relevant paths to the user.
5. **Run the cookbook command verbatim.** Don't improvise CLI flags. If the user wants a flag this skill doesn't document, fall back to the underlying Skill's `SKILL.md`.
6. **Verify output.** After any write, list the produced files with `computer://` links and print the substitution count or token count where applicable.
7. **Push back on bypass requests.** If the user asks for "a quick script that just does X", explain that the project's `CLAUDE.md` requires routing through the Skills to preserve the acceptance criteria, and offer the equivalent cookbook command instead.

## What this Skill will NEVER do

- Write inline `python-docx` or `openpyxl` code that bypasses the Skills.
- Modify files in `templates/originals/`.
- Silently overwrite files in the output directory — append a timestamp if a collision is likely.
- Run Python library files (`pipeline.py`, `tokenize_template.py`, etc.) as standalone scripts — use their public CLI wrappers.
- **Assume or hard-code a settings file.** Always ask the user which one to use.
- **Pick a settings file automatically.** User choice is mandatory, except for setup/test operations.

## Health-check checklist (before any major run)

If the user is about to do something high-stakes, run these checks first and report the results:

```bash
cd /Users/r-kawashima/Projects/Document-Modification

# 1) Ask user which settings to use
ls -1 settings/*.json
# (user selects one)

# 2) Load and validate chosen settings
CHOSEN_FILE="user_selected_file.json"
python3 -c "import json; s = json.load(open('settings/$CHOSEN_FILE')); \
  print('✓ Settings valid'); \
  print('  Template:', s.get('template_local_file')); \
  print('  Data:', s.get('source_table_file')); \
  print('  Output:', s.get('local_output_directory'))"

# 3) Engine still passes acceptance tests
python3 tests/test_docx_replacer.py

# 4) Template tokens match data columns
TEMPLATE=$(python3 -c "import json; print(json.load(open('settings/$CHOSEN_FILE')).get('template_local_file'))")
PYTHONPATH=src python3 -m doc_modifier --template "$TEMPLATE" --list-tokens

# 5) PDF backend is available (if PDF is in --formats)
which soffice libreoffice || echo "No LibreOffice; need Microsoft Word for PDF."
```

Only proceed with the user's request once all checks pass.
