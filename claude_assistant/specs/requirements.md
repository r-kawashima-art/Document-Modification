# Requirements Definition: Claude Slack Agent

## 1. Functional Requirements

### Slack Integration
- **FR1**: Listen for `@Claude Assistant` mentions in configured Slack channel
- **FR2**: Extract document generation request from Slack message
- **FR3**: Post completion report to originating Slack channel (count succeeded/failed)
- **FR4**: Post error message if request is malformed or missing required parameters

### Configuration Management
- **FR5**: Load configuration from `settings/*.json` files
- **FR6**: Validate required fields: `slack_channel_id`, `template_local_file`, `data_source_spreadsheet`, `local_output_directory`
- **FR7**: Resolve all file paths relative to workspace root
- **FR8**: Support optional `output_google_drive_directory` for cloud output (Google Drive folder URL format)
- **FR9**: Support configurable output formats (docx, pdf)

### Document Generation Workflow
- **FR10**: Load tokenized template from local filesystem
- **FR11**: Load data source (Excel) from local or Google Drive path
- **FR12**: Filter data rows where `status` column = "todo"
- **FR13**: Generate documents for filtered rows using document-modification engine
- **FR14**: Preserve original fonts and line breaks in generated documents
- **FR15**: Output generated documents to configured directory/directories

### Source Table Updates
- **FR16**: Update `status` column to "done" for each successfully generated row
- **FR17**: Keep `status` as "todo" for rows that fail document generation
- **FR18**: Persist updated source table (save Excel file or Google Sheet)
- **FR19**: Maintain all other columns unchanged during update

### Error Handling & Reporting
- **FR20**: Fail gracefully if template file does not exist or cannot be read
- **FR21**: Fail gracefully if data source file does not exist or is invalid
- **FR22**: Fail gracefully if `status` column is missing from data source
- **FR23**: Report partial success: "X/Y documents generated, Z failed"
- **FR24**: Include row identifiers and error reasons for failed rows

---

## 2. Non-Functional Requirements

### Performance & Concurrency
- **NFR1**: Support batch generation of up to 100+ rows per request
- **NFR2**: Process completes within 60 seconds for typical batches (≤50 rows)
- **NFR3**: Rate limit to 1 request per 30 seconds per Slack channel (prevent overload)
- **NFR4**: Warn if concurrent requests modify the same source table simultaneously

### Idempotency & Safety
- **NFR5**: Rerunning on same data file only processes new "todo" rows
- **NFR6**: Mark rows as "done" only after successful document generation
- **NFR7**: Prevent duplicate document generation for already-processed rows

### Data Integrity
- **NFR8**: Validate Excel headers match template token names (case-sensitive)
- **NFR9**: Do not modify or delete original source files (work on copies if needed)
- **NFR10**: Preserve status column data type (text) during update

---

## 3. Data Requirements

### Input Data
- **DR1**: Data source must be Excel (.xlsx) with a header row
- **DR2**: Data source must contain a `status` column with values: "todo", "done", "skip" (or equivalent)
- **DR3**: Other column headers must exactly match template token names

### Output Data
- **DR4**: Generated documents placed in configured output directory
- **DR5**: Generated documents named by row identifier or index (e.g., `applicant_001.docx`)
- **DR6**: Support multiple output formats per request (docx, pdf simultaneously)
- **DR7**: Updated source table saved to same location as input (overwrite or new version)

---

## 4. Integration Requirements

### Slack API
- **IR1**: Use Slack Events API or Bolt framework to listen for app mentions
- **IR2**: Post messages via Slack Web API
- **IR3**: Handle Slack token authentication securely

### Claude Cowork / Document Engine
- **IR4**: Invoke document-modification engine via MCP or direct Python module
- **IR5**: Pass template path, data file, output directory as parameters
- **IR6**: Receive generation status and error details from engine

### File Storage
- **IR7**: Support local filesystem paths (absolute or workspace-relative)
- **IR8**: Support Google Drive paths (authenticated via service account or user token)
- **IR9**: Handle path resolution transparently (local vs. cloud)

---

## 5. Acceptance Criteria (from User Story)

Maps to requirements:

| Criterion | Related Requirements | Verification Method |
|-----------|-------------------|-------------------|
| Only "todo" rows processed | FR12 | Run with mixed statuses, confirm only "todo" generated |
| Status updated to "done" | FR16, FR18 | Open source file after run, verify status column changed |
| Fonts and line breaks preserved | FR14 | Open generated document, compare formatting to template |
| Partial failures reported | FR23, FR24 | Run with invalid row (missing field), confirm "X succeeded, 1 failed" message |
| Source table persisted | FR18, NFR5 | Restart app, run again, confirm previously "done" rows skipped |
