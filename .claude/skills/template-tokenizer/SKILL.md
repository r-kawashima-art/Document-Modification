---
name: template-tokenizer
description: Use this skill whenever the user wants to CONVERT an existing Word (.docx) or Excel (.xlsx) document into a reusable tokenized template with {{snake_case}} placeholders, instead of editing it manually in Word. Trigger phrases include "テンプレ化して", "tokenize this document", "make a template from this file", "auto-detect the fields in this Word doc", "turn this invitation letter into a reusable template". Pair this skill with the document-modification skill: this one creates the template, that one fills it.
---

# template-tokenizer — Auto-create a tokenized template from any document

This skill removes the manual find-and-replace step from template onboarding (README §5). Given a source `.docx` with a label : value table, it:

1. Auto-detects fields.
2. Generates `snake_case` token names from each label.
3. Sweeps the body for inline duplicates of table values.
4. Emits a tokenized `.docx` **plus** a starter `.xlsx` data file with the right header row and one example row pre-filled.

The engine preserves fonts (フォント) and line breaks (改行) bit-for-bit — same run-aware logic the `document-modification` skill uses at render time.

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

Once the user confirms (or supplies overrides), run:

```bash
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source "<path/to/source.docx>" \
    --out "templates/<Template_Name>.docx" \
    --starter-data "data/<starter_data>.xlsx"
```

Always pass `--starter-data` unless the user already has a data file — it saves them from authoring the header row by hand.

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
    --out tokenized.docx \
    --starter-data data.xlsx
```

The mapping is merged with auto-detect (mapping wins on conflicts).

## Adding tokens to an already-tokenized template

When the user wants to add new `{{tokens}}` to a template that already has existing placeholders (e.g. adding `letter_date`, `company`, pronoun tokens), use `--no-auto-detect` so the engine only applies the explicit mapping without trying to re-tokenize existing `{{...}}` strings:

```bash
# 1. Dry-run to preview
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source templates/existing_tokenized.docx \
    --mapping data/new_tokens.yaml \
    --no-auto-detect \
    --dry-run -v

# 2. Apply (overwrites the template in-place; engine preserves all existing tokens)
PYTHONPATH=src python3 -m doc_modifier.tokenize_cli \
    --source templates/existing_tokenized.docx \
    --mapping data/new_tokens.yaml \
    --no-auto-detect \
    --out templates/existing_tokenized.docx \
    --starter-data data/updated_starter.xlsx
```

> **Longest-match safety**: the engine sorts doc-wide replacements by descending length before applying them. This means longer strings like `"his/her"` are replaced before shorter substrings like `"her"`, preventing double-replacements. Rely on this when mapping pronoun variants.

## Standard token set for the Adventure India Invitation Letter

The current tokenized template (`templates/Template_Invitation_Letter_Adventure_India_tokenized.docx`) uses these tokens:

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

1. **Locate the source.** Confirm the source `.docx` path with the user. If the user uploaded a file, copy it under `templates/originals/` (don't tokenize in place — always preserve the original).
2. **Dry-run.** Run the CLI with `--dry-run` and read the proposed plan back to the user as a table (token, original value, location).
3. **Handle ambiguity.** If the tokenizer reports an ambiguous value (e.g. "Japan" → two tokens), confirm with the user that the cell-scoped treatment is acceptable, or offer to add an explicit mapping.
4. **Confirm.** Ask the user to approve the plan and to pick the output template path.
5. **Apply.** Run the CLI again without `--dry-run`, passing `--out` and (ideally) `--starter-data`.
6. **Verify.** The CLI prints "Tokens present in output (N): …". Read those tokens back to the user and confirm they match the starter data file's header row.
7. **Hand off.** Suggest the user can now invoke the `document-modification` skill to render letters from the starter data file (or their own).

## Quality bar

- Never tokenize the user's only copy of the source document — always write to a new path.
- Never modify the source's fonts or line breaks. The engine guarantees this; double-check by counting `<w:p>` and `<w:br>` if the user is worried.
- If `--dry-run` produces zero replacements, the source has no label:value table the heuristic recognizes. Suggest the explicit-mapping mode (YAML/JSON/xlsx).
