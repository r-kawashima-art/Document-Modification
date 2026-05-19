---
name: doc-automation-runner
description: Use this skill whenever an Adventure Inc. teammate wants Claude to RUN a Python script in this repository on their behalf — tokenize a Word doc, render letters from a spreadsheet, convert a .docx to PDF, list a template's tokens, inspect a data file's columns, install dependencies, or run the test suite. This skill is the single front door for every Python entry point under src/doc_modifier/. Trigger phrases include "run the document automation", "run the python script", "do this for me with the engine", "automate this with the doc tools", "process these documents", "Pythonでやって", "実行して", "テンプレ化と差し込み両方やって". For pure tokenize-only or pure render-only requests, this skill DELEGATES to the task-specific skills (template-tokenizer / document-modification) rather than bypassing them.
---

# doc-automation-runner — single entry point for every Python script

Adventure Inc.'s administrative department (管理部) does not need to memorize which CLI does what. This skill maps any high-level request to the correct underlying Python entry point, runs it, and presents the results — without asking the user to learn `python -m doc_modifier.tokenize_cli` syntax.

## When to invoke this Skill

Invoke `doc-automation-runner` when **any** of the following are true:

- The user wants Claude to run code from this repository.
- The user describes a multi-step workflow that touches more than one script (e.g. "tokenize this AND fill it from data AND give me PDFs").
- The user wants a utility operation that has no dedicated Skill: PDF-only conversion, token inspection, test run, dependency install, data-file inspection.
- The user is unsure which tool they need — let this skill classify intent.

Do **not** invoke this Skill when the user has already named one of the task-specific skills explicitly ("use the tokenizer", "use the renderer"). In that case, invoke that skill directly.

## Intent → Action routing

Classify the user's request against this table **first**.

| Intent (利用者の意図) | Trigger phrases | Action |
|---|---|---|
| Tokenize a source document | "make a template", "テンプレ化", "tokenize this Word doc" | **Delegate** to the `template-tokenizer` Skill. Per `CLAUDE.md` §1, never bypass it. |
| Fill a template from data | "render letters", "招待状作って", "fill the template" | **Delegate** to the `document-modification` Skill. |
| Tokenize then render in one chain | "from this raw doc, produce filled PDFs", "テンプレ化してから差し込みも" | Chain both delegations in sequence (§ End-to-end chain below). |
| List tokens in a template | "what tokens does this template have?", "list the placeholders" | Run `python -m doc_modifier --template <path> --list-tokens`. |
| Inspect columns in a data .xlsx | "what columns are in this spreadsheet?", "show me the data headers" | Run a 3-line openpyxl inspector (§ Cookbook). |
| Convert a .docx (or .xlsx) to PDF only | "convert this docx to pdf", "pdf化して" | Run a one-liner that calls `doc_modifier.pdf_exporter.to_pdf()`. |
| Install / set up the project | "install dependencies", "set this up on my Mac" | Run `pip install -r requirements.txt`; suggest LibreOffice fallback for PDF. |
| Run the acceptance tests | "verify the engine", "run the tests", "check fonts and line breaks still survive" | Run `python3 tests/test_docx_replacer.py`. |
| Dry-run / preview anything | "preview only", "don't write yet", "--dry-run" | Forward the `--dry-run` flag to whichever underlying CLI applies. |

If a user request maps to more than one row, ask one clarifying question rather than guessing.

## Catalog of Python entry points

Read this once before suggesting commands; route everything through these entry points.

| Module / script | Direct CLI invocation | What it does |
|---|---|---|
| `doc_modifier.cli` | `python -m doc_modifier --template … --data … --out … --formats docx,pdf` | Renderer entry. Fills a tokenized template with rows from a data .xlsx. |
| `doc_modifier.cli` (inspect mode) | `python -m doc_modifier --template … --list-tokens` | Print every `{{token}}` referenced by a template. |
| `doc_modifier.tokenize_cli` | `python -m doc_modifier.tokenize_cli --source … --out … --starter-data …` | Tokenizer entry. Converts a source `.docx` into a tokenized template + optional starter data file. |
| `doc_modifier.tokenize_cli` (preview mode) | `python -m doc_modifier.tokenize_cli --source … --dry-run` | Print the proposed tokenization plan without writing anything. |
| `doc_modifier.pipeline` | (library only) | Orchestration used by `doc_modifier.cli`. Not invoked directly. |
| `doc_modifier.tokenize_template` | (library only) | Tokenizer engine. Not invoked directly. |
| `doc_modifier.docx_replacer` | (library only) | Run-aware `.docx` text replacement. Not invoked directly. |
| `doc_modifier.xlsx_replacer` | (library only) | Cell-level `.xlsx` token replacement. |
| `doc_modifier.xlsx_loader` | (library only) | Row loader for data files. Header normalization (`Passport No.` → `passport_no`). |
| `doc_modifier.pdf_exporter` | `python -c "from doc_modifier.pdf_exporter import to_pdf; to_pdf('<in>', '<out.pdf>')"` | docx2pdf → LibreOffice fallback. |
| `tests/test_docx_replacer.py` | `python3 tests/test_docx_replacer.py` | Framework-free acceptance tests. |

All commands assume `cd /Users/r-kawashima/Projects/Document-Modification` and `PYTHONPATH=src` are set.

## Cookbook of common operations

Use this when the user request matches one of the rows below. Run the listed bash command; **do not invent new flags**.

### 1. List the tokens a template defines

```bash
cd /Users/r-kawashima/Projects/Document-Modification && PYTHONPATH=src python3 -m doc_modifier \
    --template "<path/to/template.docx>" \
    --list-tokens
```

Read the printed list back to the user. If they are about to render, compare it to the data file's columns and surface any mismatch before the render runs.

### 2. Show the columns in a data .xlsx

```bash
cd /Users/r-kawashima/Projects/Document-Modification && python3 -c "
from openpyxl import load_workbook
wb = load_workbook('<path/to/data.xlsx>', data_only=True)
ws = wb.active
print('Sheet:', ws.title)
print('Columns:', [c.value for c in next(ws.iter_rows(max_row=1))])
print('Rows:', ws.max_row - 1)
"
```

### 3. Convert an existing `.docx` to `.pdf` (no rendering, no tokenizing)

```bash
cd /Users/r-kawashima/Projects/Document-Modification && PYTHONPATH=src python3 -c "
from doc_modifier.pdf_exporter import to_pdf
to_pdf('<input.docx>', '<output.pdf>')
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

### 5. Verify the engine (run acceptance tests)

```bash
cd /Users/r-kawashima/Projects/Document-Modification && python3 tests/test_docx_replacer.py
```

Read the `✓` lines back to the user — if any fail, do not proceed with rendering work until investigated.

### 6. End-to-end chain: source `.docx` → tokenized template → filled PDFs

This is the killer chained workflow. It calls **three** scripts in sequence:

```bash
cd /Users/r-kawashima/Projects/Document-Modification

# Step 1 — preview the tokenization
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "templates/originals/<Source.docx>" \
    --dry-run

# (Read plan back to user, confirm)

# Step 2 — apply the tokenization + emit starter data
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source       "templates/originals/<Source.docx>" \
    --out          "templates/<Template_Name>.docx" \
    --starter-data "data/starter_<name>.xlsx"

# Step 3 — render filled documents from the starter data
PYTHONPATH=src python3 -m doc_modifier \
    --template "templates/<Template_Name>.docx" \
    --data     "data/starter_<name>.xlsx" \
    --out      "output/" \
    --formats  docx,pdf
```

In Cowork chat, this collapses into a single user utterance:

> *"From `templates/originals/<Source.docx>`, make a template and render filled PDFs."*

This skill should be the one to drive the chain — but **internally it delegates the tokenize step to `template-tokenizer`** and **the render step to `document-modification`** (per `CLAUDE.md` §1). The runner's job is sequencing and verification, not bypass.

## Standard operating procedure

1. **Classify intent.** Match the user's words to one row of "Intent → Action routing".
2. **Delegate if appropriate.** For pure tokenize/render/chain requests, hand off to the task-specific Skills.
3. **Confirm inputs.** Before running anything, list the file paths Claude will read or write back to the user. If any are missing, ask the user to upload or specify.
4. **Run the cookbook command verbatim.** Don't improvise CLI flags. If the user wants a flag this skill doesn't document, fall back to the underlying Skill's `SKILL.md` (template-tokenizer / document-modification).
5. **Verify output.** After any write, list the produced files with `computer://` links and print the substitution count or token count where applicable.
6. **Push back on bypass requests.** If the user asks for "a quick script that just does X", explain that the project's `CLAUDE.md` requires routing through the Skills to preserve the acceptance criteria (fonts / 改行), and offer the equivalent cookbook command instead.

## What this Skill will NEVER do

- Write inline `python-docx` or `openpyxl` code that bypasses `tokenize_template.py` or `docx_replacer.py`. (Per `CLAUDE.md` §3.)
- Modify files in `templates/originals/`.
- Silently overwrite files in `output/` — append a timestamp if a collision is likely.
- Run any of the Python files (`pipeline.py`, `tokenize_template.py`, `docx_replacer.py`, `xlsx_replacer.py`, `xlsx_loader.py`, `pdf_exporter.py`) as standalone scripts — they are library modules. Use their public CLI wrappers.

## Health-check checklist (before any major run)

If the user is about to do something high-stakes (e.g. render 50 invitation letters for a real visa application), run these three checks first and report the results:

```bash
cd /Users/r-kawashima/Projects/Document-Modification

# 1) Engine still passes acceptance tests
python3 tests/test_docx_replacer.py

# 2) Template tokens match data columns
PYTHONPATH=src python3 -m doc_modifier --template "<tpl>" --list-tokens

# 3) PDF backend is available (if PDF is in --formats)
which soffice libreoffice || echo "No LibreOffice; need Microsoft Word for PDF."
```

Only proceed with the user's request once all three pass.
