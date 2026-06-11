# User Story: Claude Slack Agent for Document Automation

## Business Value (Why)

Enable non-technical users in Slack to trigger document generation (招待状, 依頼書, etc.) without leaving their chat interface, reducing manual work and improving collaboration between administrative teams and Claude.

## Feature Definition (What)

**As a** Slack user in the administrative department,  
**I want to** mention @Claude Assistant in a Slack message with a document request,  
**So that** Claude automatically generates filled documents from a tokenized template and reports completion in the same Slack channel.

## User Flow

1. User posts in Slack: `@Claude Assistant create documents from {{template_name}} using {{data_file}}`
2. Slack app listens for mentions, extracts context from configured `settings/*.json`
3. App forwards the request to Claude Cowork (via MCP or API call)
4. Claude Cowork:
   - Loads the tokenized template from local filesystem
   - Loads the data source (Excel) from either local or Google Drive
   - Renders documents to specified output location
   - Reports success/failure with file count and formats generated
5. App posts completion message in the originating Slack channel with download links (if applicable)

## Configuration (settings/*.json schema)

```json
{
  "slack_channel_id": "C01234567890",
  "template_local_file": "templates/invitation_letter.docx",
  "data_source_spreadsheet": "data/applicants_2026.xlsx",
  "local_output_directory": "./output/",
  "output_Google_drive_directory": "drive://My Drive/Generated Docs/",
  "output_formats": ["docx", "pdf"]
}
```

| Field | Description | Example |
|-------|-------------|---------|
| `slack_channel_id` | Slack channel to send/receive messages | `C01234567890` |
| `template_local_file` | Path to tokenized template (with `{{tokens}}`) | `templates/invitation_letter.docx` |
| `data_source_spreadsheet` | Path to Excel data file with headers matching template tokens | `data/applicants_2026.xlsx` |
| `local_output_directory` | Local filesystem path for generated documents | `./output/` |
| `output_Google_drive_directory` | (Optional) Google Drive folder for generated documents | `https://drive.google.com/drive/folders/1ELyFup7-8zTd3fl2JLRmY41wcRN1Sf6y?usp=drive_link` |
| `output_formats` | Document formats to generate | `["docx", "pdf"]` |

## Acceptance Criteria

- **AC-1**: Slack listener detects `@Claude Assistant` mentions and extracts the request
- **AC-2**: Claude receives the request and validates that template and data files exist before processing
- **AC-3**: Generated documents preserve original fonts and line breaks
- **AC-4**: App reports success with count of filled documents per output format
- **AC-5**: App reports errors with actionable message if template or data file is missing/invalid
- **AC-6**: All file paths in `settings/*.json` are resolved relative to workspace root
- **AC-7**: Only rows with status = "todo" are processed
- **AC-8**: Status is updated to "done" after successful generation
- **AC-9**: Source table changes are persisted (local or Google Sheet)
- **AC-10**: Non-"todo" rows are silently skipped

## Constraints & Edge Cases

- **No manual template edits**: Only pre-tokenized templates (with `{{snake_case}}` placeholders) are supported
- **Data file validation**: Excel headers must exactly match template token names (case-sensitive)
- **Async reporting**: Slack message posts after document generation completes (may take 10+ seconds for large batches)
- **Rate limiting**: Max 1 document generation request per 30 seconds per channel to avoid overload
- **Partial failures**: If 1 of 100 rows fails, report "98/100 succeeded" with failing row details