# Design

Technical "How" for the requirements in `requirements.md`. Architecture, state machine, directory tree.

## 1. Architecture Overview

The system has **three layers** that work together:

1. a **workflow layer** that accepts requests from Slack, routes approval, and tracks job state,
2. a **document engine** that tokenizes templates and renders approved jobs, and
3. a **delivery layer** that writes local outputs, syncs to Google Drive, and posts completion notices back to Slack.

The tokenizer and renderer still share the same run-aware text-mutation core; the workflow layer simply decides when and how that core is invoked.

```mermaid
flowchart LR
    SLACK[Slack request<br/>intake channel] --> WF[Workflow orchestrator<br/>doc_modifier.workflow]
    APPROVAL[Approval Slack channel] --> WF
    WF --> P[Pipeline<br/>doc_modifier.pipeline]

    SRC[Source .docx<br/>templates/originals/] --> TOK[Tokenizer<br/>doc_modifier.tokenize_template]
    MAP[Optional mapping<br/>.yaml / .json / .xlsx] -.-> TOK
    TOK --> TPL[Tokenized template<br/>templates/*.docx]
    TOK --> SD[Starter data<br/>data/*.xlsx]

    DATA[Data .xlsx<br/>data/] --> P
    TPL --> P
    SD -.->|optional seed| DATA

    P --> R[Replacer<br/>docx_replacer / xlsx_replacer]
    R --> O1[Rendered .docx]
    R --> O2[Rendered .xlsx]
    O1 -- pdf_exporter --> O3[.pdf]
    O2 -- pdf_exporter --> O3
    O1 --> DRIVE[Google Drive sync<br/>doc_modifier.drive_client]
    O2 --> DRIVE
    O3 --> DRIVE
    O1 --> LOCAL[Local output<br/>/output/]
    O2 --> LOCAL
    O3 --> LOCAL
    DRIVE --> DONE[Slack completion notice]

    subgraph Tokenizer Frontends
      ST[template-tokenizer<br/>Cowork Skill]
      CT[python -m doc_modifier<br/>.tokenize_cli]
    end
    subgraph Renderer Frontends
      SR[document-modification<br/>Cowork Skill]
      CR[python -m doc_modifier]
    end
    ST --> TOK
    CT --> TOK
    SR --> P
    CR --> P
```

The tokenizer is **upstream** of the renderer: a source `.docx` flows through the tokenizer once per document type, then the workflow layer invokes the renderer once per approved batch of applicants.

## 2. Component Responsibilities

| Module | Responsibility |
|--------|----------------|
| `doc_modifier.xlsx_loader` | Read the data .xlsx; yield row dicts keyed by header column (`name`, `passport_no`, …). |
| `doc_modifier.docx_replacer` | **Run-aware** (`run` = `<w:r>` element) token replacement inside `.docx`. Preserves `<w:rPr>` so fonts, sizes, weights, line breaks are untouched. Handles tokens split across runs by merging adjacent same-format runs only when a `{{` is detected. |
| `doc_modifier.xlsx_replacer` | Cell-by-cell token replacement for `.xlsx` templates via `openpyxl`. |
| `doc_modifier.pdf_exporter` | Convert rendered `.docx` / `.xlsx` to `.pdf`. Tries `docx2pdf` (Word) → `soffice --headless --convert-to pdf` (LibreOffice) → raises informative error. |
| `doc_modifier.pipeline` | Orchestrates: load rows → render template per row → optionally export PDF → write outputs to `/output/`. |
| `doc_modifier.workflow` | Orchestrates the Slack intake, approval gate, job persistence, rendering pipeline, Drive sync, and completion notification. |
| `doc_modifier.slack_client` | Receives intake messages, posts approval requests, and sends completion notices. |
| `doc_modifier.drive_client` | Uploads rendered outputs to the configured Google Drive folder and returns shareable destinations. |
| `doc_modifier.job_store` | Persists job status, approval metadata, timestamps, and output paths for auditability and retries. |
| `doc_modifier.cli` | `argparse`-based entrypoint for the renderer. Validates inputs, prints progress, supports `--list-tokens`. |
| `doc_modifier.tokenize_template` | **Auto-tokenizer engine.** Detects label:value tables, generates `snake_case` tokens, flags ambiguous values (same text → multiple tokens) as cell-scoped, and sweeps body paragraphs for unambiguous inline duplicates. Builds a `TokenizationPlan` dataclass and applies it via the same run-aware replacement the renderer uses, so fonts (フォント) and line breaks (改行) survive. Also exports `emit_starter_data()` to seed the data file. |
| `doc_modifier.tokenize_cli` | `argparse`-based entrypoint for the tokenizer (`python -m doc_modifier.tokenize_cli`). Flags: `--source`, `--out`, `--mapping`, `--no-auto-detect`, `--starter-data`, `--dry-run`. |

## 3. State Transition

### 3.0 Workflow FSM

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Capturing: Slack request received
    Capturing --> AwaitingApproval: job stored + approval requested
    AwaitingApproval --> Rejected: approver rejects
    AwaitingApproval --> Generating: approver approves
    Generating --> DeliveringLocal: render completes
    DeliveringLocal --> DeliveringDrive: local save completes
    DeliveringDrive --> Notifying: Drive upload completes
    Notifying --> Done: Slack completion sent
    DeliveringLocal --> Failed: render/write failure
    DeliveringDrive --> Failed: Drive upload failure
    Notifying --> Failed: Slack notification failure
    Rejected --> Done
    Failed --> [*]
    Done --> [*]
```

**End condition:** the request is either rejected and closed, or approved and fully processed with local output, Google Drive delivery, and Slack completion notification recorded.

### 3.1 Renderer FSM

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Validating: cli.main(args)
    Validating --> Failed: missing template / data / mismatched headers
    Validating --> Loading: inputs OK
    Loading --> Rendering: rows loaded (N rows)
    Rendering --> Rendering: row i → render → write
    Rendering --> Exporting: all rows rendered & --pdf flag set
    Rendering --> Done: all rows rendered & no PDF
    Exporting --> Done: PDF produced for each output
    Exporting --> Failed: no PDF backend found
    Failed --> [*]
    Done --> [*]
```

**End condition (終了条件):** every row in the data .xlsx has produced exactly one rendered output (`.docx`/`.xlsx`) and, if `--pdf` was passed, exactly one matching `.pdf`.

### 3.2 Tokenizer FSM

```mermaid
stateDiagram-v2
    [*] --> TIdle
    TIdle --> Analyzing: tokenize_cli.main(args)
    Analyzing --> TFailed: source missing / unreadable
    Analyzing --> Planning: source loaded
    Planning --> Ambiguity: any value maps to multiple tokens
    Planning --> ReadyToApply: all replacements unambiguous
    Ambiguity --> ReadyToApply: kept cell-scoped + warning emitted
    ReadyToApply --> Printed: --dry-run path
    ReadyToApply --> Applied: write tokenized .docx
    Applied --> EmittedData: --starter-data provided
    Applied --> TDone: no starter requested
    EmittedData --> TDone
    Printed --> TDone
    TFailed --> [*]
    TDone --> [*]
```

**End condition:** in `--dry-run`, the proposed plan is fully printed and no files are touched. Otherwise, the tokenized `.docx` exists at `--out`, optionally accompanied by a starter `.xlsx` at `--starter-data`, and every ambiguity has been surfaced to the user as a warning.

## 4. Core Algorithms

### 4.1 Run-aware replacement (used by both renderer and tokenizer)

The hardest part of `.docx` editing is that Word frequently splits a single visible string across multiple `<w:r>` runs (e.g., `{{na` in run 5, `me}}` in run 6) because of invisible spell-check or formatting boundaries. A naïve `paragraph.text.replace(...)` would destroy fonts because reassigning `paragraph.text` collapses all runs into one and discards their individual `<w:rPr>`.

Our algorithm preserves formatting:

1. For each paragraph (and each table cell paragraph), walk the runs in order and build a flat list of `(run_index, char_index_in_run)` → `char` map.
2. Concatenate run texts into a single buffer and locate every target occurrence (a `{{key}}` for the renderer, or a literal sample value for the tokenizer) by regex / substring search.
3. For each match, identify the **starting run**, set its text to `prefix + replacement`, set the text of all subsequent runs that contributed to the match to `""`, and (if the match's tail belongs to a later run) append that run's suffix to the starting run's text.
4. Because we only ever modify `run.text` (never `run.font` or the parent `<w:rPr>`), font attributes survive unchanged. Because we never insert/remove `<w:p>` or `<w:br>`, line breaks survive unchanged.

This algorithm runs over body paragraphs, table cells, and headers/footers. For `.xlsx`, the equivalent is `cell.value = cell.value.replace(...)` — cell-level formatting in openpyxl is stored separately and is unaffected.

### 4.2 Tokenization plan (tokenizer-specific)

The tokenizer's job is to **decide what to replace** before §4.1 is invoked. It produces a `TokenizationPlan` — a list of `Replacement(original, token, label, location, cell_addr, example_value)` records — in three passes:

1. **Auto-detect tables.** For every `<w:tbl>` in the source, evaluate the *label : value* heuristic (≥2 rows, every row's column 0 is a short label without sentence punctuation, every row's last column is a non-empty short value). If it passes, each row produces one **cell-scoped** replacement: `(table_idx, row_idx, last_col_idx)` paired with `snake_case(label)` as the token.

2. **Merge explicit overrides.** If the user supplied a `--mapping` file (`.yaml` / `.json` / `.xlsx`), each entry becomes either a **doc-wide** replacement (if `cell_addr` is empty) or replaces the token name on a previously-staged auto-detected entry.

3. **Body sweep with ambiguity guard.** For every `original` text that has been staged, count how many distinct tokens are associated with it. If exactly one → the value is *unambiguous* and the tokenizer scans body paragraphs (outside tables) for literal occurrences, adding doc-wide replacements that reuse the same token. If more than one (e.g. two table rows both containing "Japan") → the value is *ambiguous*; the tokenizer leaves both replacements cell-scoped and records a warning. The body is **not** swept for ambiguous values, preventing the wrong token from leaking into inline text.

At apply time, cell-scoped replacements are written into the specific cell only (via `doc.tables[ti].rows[ri].cells[ci]`), and doc-wide replacements are applied via §4.1 across the entire document. Cell-scoped replacements run first, sorted by descending `len(original)` so substrings never shadow longer matches.

## 5. Directory Structure

```
/Document-Modification/
├── CLAUDE.md                            # Cowork Skill routing rules
├── README.md
├── requirements.txt
├── .claude/
│   ├── CLAUDE.md                        # SDD Technical Architect persona
│   └── skills/
│       ├── document-modification/
│       │   └── SKILL.md                 # Renderer Cowork Skill
│       └── template-tokenizer/
│           └── SKILL.md                 # Tokenizer Cowork Skill
├── specs/
│   ├── user_story.md                    # The "Why"
│   ├── requirements.md                  # The "What"
│   ├── design.md                        # The "How" (this file)
│   └── implementation_plan.md           # The "When"
├── docs/
│   └── walkthrough.md                   # The "Proof"
├── src/
│   └── doc_modifier/
│       ├── __init__.py
│       ├── __main__.py                  # python -m doc_modifier (renderer)
│       ├── cli.py                       # renderer CLI
│       ├── workflow.py                  # Slack approval workflow
│       ├── pipeline.py                  # renderer orchestration
│       ├── xlsx_loader.py
│       ├── docx_replacer.py             # run-aware token replacement
│       ├── xlsx_replacer.py
│       ├── pdf_exporter.py
│       ├── slack_client.py              # Slack intake / approval / notification
│       ├── drive_client.py              # Google Drive upload
│       ├── job_store.py                 # audit trail / request state
│       ├── tokenize_template.py         # tokenizer engine
│       └── tokenize_cli.py              # python -m doc_modifier.tokenize_cli
├── templates/
│   ├── originals/                       # sources, never modified in place
│   │   └── Template_Invitation letter_Adventure India.docx
│   ├── Template_Invitation_Letter_Adventure_India_tokenized.docx   # hand-built
│   └── Template_Invitation_Letter_Adventure_India_auto.docx        # tokenizer output
├── data/
│   ├── sample_data.xlsx                 # 2 example applicants
│   └── _starter_invitation.xlsx         # tokenizer-emitted starter file
├── output/                              # generated files (gitignored)
└── tests/
    └── test_docx_replacer.py
```

## 6. Data Contracts

### 6.1 Renderer data file (`data/*.xlsx`)

The Excel data file (e.g. `sample_data.xlsx`) **MUST** have a header row with at least these columns when rendering the default invitation-letter template:

| Column header (case-insensitive) | Token rendered into template |
|---|---|
| `name` | `{{name}}` |
| `date_of_birth` | `{{date_of_birth}}` |
| `nationality` | `{{nationality}}` |
| `passport_no` | `{{passport_no}}` |
| `passport_issuing_country` | `{{passport_issuing_country}}` |
| `date_of_issue` | `{{date_of_issue}}` |
| `date_of_expiry` | `{{date_of_expiry}}` |
| `mobile_no` | `{{mobile_no}}` |

Optional column: `output_filename` — if absent, falls back to `letter_<row>_<sanitized_name>.docx`.

Header text is normalized by stripping punctuation and lowercasing, so `Passport No.` and `passport_no` are accepted equivalently.

### 6.2 Tokenizer mapping file (`--mapping`)

When the user provides `--mapping`, the file format is one of:

- **YAML** — `original text: token_name` (keys are the exact source text; values are the token name without `{{ }}`).
- **JSON** — `{"original text": "token_name"}`.
- **XLSX** — two columns, header row `original | token`.

The mapping is merged with the auto-detect plan; conflicts are resolved in favor of the mapping. With `--no-auto-detect`, only the mapping is used.

### 6.3 Starter data file (`--starter-data`)

The tokenizer emits an `.xlsx` whose header row is exactly the tokens it staged (in first-occurrence order) plus `output_filename`. Row 2 contains the original sample values from the source — useful as an immediate smoke-test render. Users can append additional rows in Excel.

## 7. Error Handling

### 7.1 Renderer

| Condition | Behavior |
|-----------|----------|
| Token in template not found in data row | Log warning; leave placeholder untouched; do not crash. |
| Column in data not referenced by any token | Log info; ignore. |
| PDF backend missing | Skip PDF for that row; print actionable hint. |
| Data file empty | Exit 2 with message "No rows to render." |

### 7.2 Tokenizer

| Condition | Behavior |
|-----------|----------|
| Source file missing or unreadable | Exit 2 with message; do not write any output. |
| Auto-detect finds zero label:value tables | Plan has 0 replacements; user is told to supply `--mapping` or `--no-auto-detect`. |
| Ambiguous value (same text maps to multiple tokens) | Both replacements kept cell-scoped; warning emitted; body sweep skipped for that value. |
| Output path already exists | Overwrite is allowed at CLI level; the `template-tokenizer` Skill SOP requires user confirmation first (per `CLAUDE.md` §2). |
| Source path equals `--out` path | Refuse to apply (would destroy the source); raise immediately. |
| Mapping file references YAML but PyYAML missing | Raise `RuntimeError` with hint `pip install pyyaml`. |

## 8. Frontend Mapping (Skill ↔ CLI)

Both engines are exposed twice — once as a Cowork Skill (natural-language UX) and once as a CLI (terminal / automation). The mapping is:

| Engine | Cowork Skill (`SKILL.md` location) | CLI invocation |
|---|---|---|
| Tokenizer | `.claude/skills/template-tokenizer/SKILL.md` | `python -m doc_modifier.tokenize_cli --source … --out … --starter-data …` |
| Renderer | `.claude/skills/document-modification/SKILL.md` | `python -m doc_modifier --template … --data … --out …` |

The routing rules in the project-root `CLAUDE.md` mandate that Claude (Cowork) **always** invoke the relevant Skill rather than write ad-hoc Python, ensuring NFR-1 / NFR-2 / NFR-6 are enforced uniformly.
