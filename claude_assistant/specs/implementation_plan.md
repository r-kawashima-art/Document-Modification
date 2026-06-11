# Implementation Plan: Claude Slack Agent

**Phase Overview**: 9 phases, ~5-7 weeks of development with iterative testing.

**Toolchain**: `uv` for Python dependency management and virtual environments.

---

## Phase 1: Project Setup & Infrastructure (with uv)

### Task 1.1: Initialize Project Structure with `uv`
**Status**: `[done]` ✅ (2026-06-11)

**Description**: Create directory structure, initialize Python environment with `uv`, and install dependencies.

**Related Requirements**: (Foundation for all FR/NFR)

**Acceptance Criteria**:
- Directory tree matches design.md §7 ✓
- `uv` virtual environment initialized ✓
- `pyproject.toml` defines all dependencies (slack-bolt, openpyxl, google-auth-oauthlib, pydantic) ✓
- `uv.lock` file generated (deterministic dependencies) ✓
- `pytest` configured with `tests/` discovery ✓
- `.gitignore` includes `settings/*.json` (except template), `__pycache__`, `.env`, credentials, `.venv` ✓

**Test Command**:
```bash
cd /Users/r-kawashima/Projects/Document-Modification
uv --version
uv sync
source .venv/bin/activate
python -c "import slack_bolt; import openpyxl; import pydantic; print('✓ All dependencies installed')"
find claude_assistant -type f -name "*.py" -not -path "*.venv*" | head -10
ls -la claude_assistant/tests/ claude_assistant/src/ claude_assistant/specs/
```

**Actual Output** (✅ Verified):
```
uv 0.11.16 (135a36367 2026-05-21 aarch64-apple-darwin)

Resolved 57 packages in 100ms
✓ All dependencies installed

./claude_assistant/src/models.py
./claude_assistant/src/__init__.py
./claude_assistant/tests/__init__.py
./claude_assistant/tests/unit/__init__.py
./claude_assistant/tests/integration/__init__.py
./claude_assistant/tests/fixtures/__init__.py
./claude_assistant/tests/unit/test_models.py

tests/ (unit, integration, fixtures subdirectories)
src/ (models.py, __init__.py)
specs/ (user_story.md, requirements.md, design.md, implementation_plan.md)
```

**Verification**: 
- `uv sync` completes without errors
- `uv.lock` file present and committed
- Virtual environment activated, all imports work
- Pytest can discover tests in `tests/`

---

### Task 1.2: Define Data Models (Pydantic)
**Status**: `[done]` ✅ (2026-06-11)

**Description**: Create `src/models.py` with Config, GenerationResult, StatusUpdate dataclasses.

**Related Requirements**: FR5, FR6, DR1-DR7

**Acceptance Criteria**:
- Config model validates required fields (slack_channel_id, template_local_file, etc.)
- GenerationResult captures success count, failed rows, error details
- StatusUpdate captures row identifier, old status, new status, reason
- All models support JSON serialization

**Test Command**:
```bash
source .venv/bin/activate
python -m pytest claude_assistant/tests/unit/test_models.py -v
```

**Test File**: `claude_assistant/tests/unit/test_models.py`

**Test Cases** (11 total):
1. `test_config_valid_all_fields` — Config with all fields validates ✓
2. `test_config_missing_required_field` — Config missing slack_channel_id raises ValidationError ✓
3. `test_config_optional_output_fields` — Config without local_output_directory and output_google_drive_directory is valid ✓
4. `test_config_json_serialization` — Config converts to/from JSON ✓
5. `test_config_invalid_output_format` — Config with invalid format raises ValidationError ✓
6. `test_generation_result_all_success` — GenerationResult with 100% success rate ✓
7. `test_generation_result_partial_success` — GenerationResult with partial failures ✓
8. `test_generation_result_json_serialization` — Result converts to/from JSON ✓
9. `test_status_update_captures_all_data` — StatusUpdate includes all fields ✓
10. `test_status_update_invalid_status` — StatusUpdate with invalid status raises ValidationError ✓
11. `test_status_update_json_serialization` — StatusUpdate converts to/from JSON ✓

**Actual Output** (✅ Verified 2026-06-11):
```
======================== 11 passed in 0.05s ========================
```

**Verification**: ✅ All 11 tests pass; models printable and serializable.

**Implementation Notes**:
- Used Pydantic v2 (modern, fastest validation)
- Config made with optional output paths (local_output_directory, output_google_drive_directory)
- All models support JSON round-trip serialization
- Zero custom logic beyond Pydantic validators

---

## Phase 1: Status Summary

**Completion**: ✅ 100% (2/2 tasks completed)
- Task 1.1: Initialize Project Structure — ✅ DONE (2026-06-11)
- Task 1.2: Define Data Models — ✅ DONE (2026-06-11)

**Deliverables**:
- ✅ Project structure created (src/, tests/unit, tests/integration, tests/fixtures, specs/, settings/)
- ✅ Root `.venv` initialized with `uv` (Python 3.14, 57 packages)
- ✅ `uv.lock` generated (deterministic dependencies)
- ✅ `pyproject.toml` configured with workspace (includes claude_assistant)
- ✅ 3 Pydantic models fully implemented and tested (11 unit tests)
- ✅ `.env.example` configured (SLACK_BOT_TOKEN, SLACK_AGENT_TOKEN, ANTHROPIC_API_KEY, etc.)
- ✅ `docs/walkthrough.md` tracking progress

**Test Coverage**: 11/11 tests passing (0.05s execution)

**Ready to proceed** → Phase 2: Minimum Viable Product (MVP)

---

## Phase 2: Minimum Viable Product (MVP)

**Objective**: Establish the core integration: Slack receives mention of @Claude Assistant → forwards request to Claude Cowork. This is the minimum working integration before adding document generation logic.

### Task 2.1: Slack Event Listener (MVP)
**Status**: `[todo]`

**Description**: Create `src/slack_listener.py` with Slack Events API listener using slack-bolt. Detect `@Claude Assistant` mentions and extract basic context (channel ID, user).

**Environment Variables Required**:
- `SLACK_AGENT_TOKEN` (xapp-...) — Agent token for receiving Events API events
- `SLACK_BOT_TOKEN` (xoxb-...) — Bot token for posting messages to Slack

**Related Requirements**: FR1, FR2, IR1, IR2, IR3

**Acceptance Criteria**:
- Slack agent receives and validates Events API events using SLACK_AGENT_TOKEN ✓
- Detects `app_mention` events for @Claude Assistant ✓
- Extracts channel ID and user ID from event ✓
- Posts acknowledgment message ("Processing request...") using SLACK_BOT_TOKEN ✓
- Logs events for debugging ✓

**Test Command**:
```bash
cd /Users/r-kawashima/Projects/Document-Modification/claude_assistant
python -m pytest tests/unit/test_slack_listener.py -v
```

**Test File**: `tests/unit/test_slack_listener.py`

**Test Cases** (mocked Slack API):
1. `test_slack_event_app_mention_detected` — Events API webhook payload → app_mention extracted ✓
2. `test_extract_channel_id_from_event` — Event payload → channel ID "C01234567890" extracted ✓
3. `test_extract_user_id_from_event` — Event payload → user ID "U01234567890" extracted ✓
4. `test_ignore_non_mention_events` — message_changed event → ignored silently ✓
5. `test_post_acknowledgment_message` — After mention detected, post "Processing..." to channel ✓
6. `test_event_logging_for_debugging` — Events logged with timestamp and channel ✓

**Expected Output**:
```
tests/unit/test_slack_listener.py::test_slack_event_app_mention_detected PASSED
tests/unit/test_slack_listener.py::test_extract_channel_id_from_event PASSED
tests/unit/test_slack_listener.py::test_extract_user_id_from_event PASSED
tests/unit/test_slack_listener.py::test_ignore_non_mention_events PASSED
tests/unit/test_slack_listener.py::test_post_acknowledgment_message PASSED
tests/unit/test_slack_listener.py::test_event_logging_for_debugging PASSED

======================== 6 passed in 0.10s ========================
```

**Verification**: Slack events received correctly, context extracted, acknowledgment posted.

---

### Task 2.2: Claude Cowork Forwarder (MVP)
**Status**: `[todo]`

**Description**: Create `src/cowork_forwarder.py` to forward requests from Slack to Claude Cowork via MCP or API.

**Related Requirements**: IR4, IR5, IR6

**Acceptance Criteria**:
- Receive extraction from slack_listener (channel ID, user ID, message) ✓
- Forward request to Claude Cowork (via MCP WebSocket or REST API) ✓
- Include context: slack_channel_id, user_id, original_message ✓
- Receive confirmation from Claude Cowork ✓
- Log forwarding event (channel, timestamp, status) ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_cowork_forwarder.py -v
```

**Test File**: `tests/unit/test_cowork_forwarder.py`

**Test Cases** (mocked Claude Cowork):
1. `test_forward_request_to_cowork` — Request forwarded with all context ✓
2. `test_include_slack_metadata_in_request` — Payload includes channel_id, user_id ✓
3. `test_receive_cowork_confirmation` — Response received, status logged ✓
4. `test_cowork_connection_failure_handled` — Connection error caught, logged, notification posted ✓
5. `test_forward_message_preserved` — Original Slack message preserved in request ✓

**Expected Output**:
```
tests/unit/test_cowork_forwarder.py::test_forward_request_to_cowork PASSED
tests/unit/test_cowork_forwarder.py::test_include_slack_metadata_in_request PASSED
tests/unit/test_cowork_forwarder.py::test_receive_cowork_confirmation PASSED
tests/unit/test_cowork_forwarder.py::test_cowork_connection_failure_handled PASSED
tests/unit/test_cowork_forwarder.py::test_forward_message_preserved PASSED

======================== 5 passed in 0.08s ========================
```

**Verification**: Requests forwarded to Claude Cowork, confirmation received, errors handled.

---

### Task 2.3: MVP Integration Test
**Status**: `[todo]`

**Description**: End-to-end test of MVP: Slack mention → forward to Claude Cowork → confirmation.

**Related Requirements**: FR1, FR2, FR3, FR4

**Acceptance Criteria**:
- Slack event triggers listener ✓
- Context extracted (channel ID, user ID) ✓
- Request forwarded to Claude Cowork ✓
- Acknowledgment posted to Slack ✓
- Success logged ✓

**Test Command**:
```bash
python -m pytest tests/integration/test_mvp_slack_to_cowork.py -v -s
```

**Test File**: `tests/integration/test_mvp_slack_to_cowork.py`

**Test Case**:
1. `test_mvp_slack_mention_to_cowork_forward`:
   - Simulate Slack event: `@Claude Assistant help me generate documents`
   - Verify listener detects mention ✓
   - Verify forward request sent to Claude Cowork with:
     - `slack_channel_id: "C01234567890"`
     - `user_id: "U01234567890"`
     - `message: "help me generate documents"`
   - Verify acknowledgment posted: "Processing your request..." ✓
   - Verify log entry recorded ✓

**Expected Output**:
```
tests/integration/test_mvp_slack_to_cowork.py::test_mvp_slack_mention_to_cowork_forward PASSED

Logs:
  [INFO] Slack event received: app_mention in channel C01234567890
  [INFO] Extracting context: user=U01234567890, message="help me generate documents"
  [INFO] Posting acknowledgment to channel C01234567890
  [INFO] Forwarding request to Claude Cowork (endpoint: /cowork/tasks)
  [INFO] Confirmation received from Claude Cowork
  [SUCCESS] MVP workflow complete: Slack → Claude Cowork
```

**Verification**: Full MVP workflow completes without errors; all components communicate.

---

## Phase 3: Configuration Management

### Task 3.1: Implement ConfigManager
**Status**: `[todo]`

**Description**: Create `src/config_manager.py` to load, validate, and resolve file paths in settings/*.json.

**Related Requirements**: FR5, FR6, FR7

**Acceptance Criteria**:
- Load JSON from specified settings file ✓
- Validate all required fields present ✓
- Resolve local paths relative to workspace root ✓
- Raise ConfigError with actionable message if validation fails ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_config_manager.py -v
```

**Test File**: `tests/unit/test_config_manager.py` (Phase 3)

**Test Fixtures**:
- `tests/fixtures/sample_config.json` — Valid config with all fields
- `tests/fixtures/invalid_config.json` — Missing required field
- `tests/fixtures/config_with_gd.json` — Valid config with Google Drive path

**Test Cases**:
1. `test_load_valid_config` — Loads valid JSON, returns Config object ✓
2. `test_validate_required_fields` — Detects missing slack_channel_id ✓
3. `test_validate_required_fields_template` — Detects missing template_local_file ✓
4. `test_resolve_local_paths` — Resolves ./templates/ to absolute path ✓
5. `test_invalid_json_raises_error` — Malformed JSON raises JSONDecodeError ✓
6. `test_google_drive_url_accepted` — Parses GDrive URL and extracts folder_id ✓

**Expected Output**:
```
tests/unit/test_config_manager.py::test_load_valid_config PASSED
tests/unit/test_config_manager.py::test_validate_required_fields PASSED
tests/unit/test_config_manager.py::test_validate_required_fields_template PASSED
tests/unit/test_config_manager.py::test_resolve_local_paths PASSED
tests/unit/test_config_manager.py::test_invalid_json_raises_error PASSED
tests/unit/test_config_manager.py::test_google_drive_url_accepted PASSED

======================== 6 passed in 0.08s ========================
```

**Verification**: Config loads, paths resolve correctly, errors are descriptive.

---

## Phase 4: File Storage Abstraction

### Task 4.1: Implement FileStorage (Local)
**Status**: `[todo]`

**Description**: Create `src/file_storage.py` with LocalFileStorage class. Support read/write for local .xlsx and .docx files.

**Related Requirements**: FR10, FR11, IR7

**Acceptance Criteria**:
- Read Excel file into list of dicts (each row) ✓
- Write updated Excel file with new status column ✓
- Preserve all original columns and order ✓
- Raise FileNotFoundError if file doesn't exist ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_file_storage.py::test_local_* -v
```

**Test File**: `tests/unit/test_file_storage.py`

**Test Fixtures**:
- `tests/fixtures/sample_data.xlsx` — 3 rows with columns: name, email, status
- `tests/fixtures/nonexistent.xlsx` — Non-existent file

**Test Cases**:
1. `test_local_read_excel` — Reads 3 rows, preserves all columns ✓
2. `test_local_read_preserves_column_order` — Column order matches original ✓
3. `test_local_read_status_column` — Status values are strings (todo/done) ✓
4. `test_local_read_nonexistent_raises_error` — FileNotFoundError raised ✓
5. `test_local_write_excel` — Writes updated rows to new file ✓
6. `test_local_write_preserves_columns` — All original columns intact ✓
7. `test_local_write_status_updated` — Status column reflects updates ✓

**Expected Output**:
```
tests/unit/test_file_storage.py::test_local_read_excel PASSED
tests/unit/test_file_storage.py::test_local_read_preserves_column_order PASSED
tests/unit/test_file_storage.py::test_local_read_status_column PASSED
tests/unit/test_file_storage.py::test_local_read_nonexistent_raises_error PASSED
tests/unit/test_file_storage.py::test_local_write_excel PASSED
tests/unit/test_file_storage.py::test_local_write_preserves_columns PASSED
tests/unit/test_file_storage.py::test_local_write_status_updated PASSED

======================== 7 passed in 0.12s ========================
```

**Verification**: Files read/written correctly, columns preserved, status updates reflected.

---

### Task 4.2: Implement FileStorage (Google Drive) — Optional/Phase 2
**Status**: `[todo]`

**Description**: Extend FileStorage with GoogleDriveStorage class. Read/write via Google Drive API v3.

**Related Requirements**: IR8

**Acceptance Criteria**:
- Download file from GDrive folder by file name ✓
- Upload updated file to GDrive folder ✓
- Handle auth errors gracefully (fallback to local) ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_file_storage.py::test_gd_* -v
```

**Test Cases**:
1. `test_gd_extract_folder_id_from_url` — Parses folder_id from GDrive URL ✓
2. `test_gd_download_file_mocked` — Mock API call, verify file downloaded ✓
3. `test_gd_upload_file_mocked` — Mock API call, verify file uploaded ✓
4. `test_gd_auth_failure_fallback` — Catches AuthError, warns user ✓

**Expected Output**:
```
tests/unit/test_file_storage.py::test_gd_extract_folder_id_from_url PASSED
tests/unit/test_file_storage.py::test_gd_download_file_mocked PASSED
tests/unit/test_file_storage.py::test_gd_upload_file_mocked PASSED
tests/unit/test_file_storage.py::test_gd_auth_failure_fallback PASSED

======================== 4 passed in 0.10s ========================
```

---

## Phase 5: Request Orchestration (Core Logic)

### Task 5.1: Implement RequestOrchestrator — Status Filtering
**Status**: `[todo]`

**Description**: Create `src/request_orchestrator.py` with filter_by_status() method.

**Related Requirements**: FR12, FR22

**Acceptance Criteria**:
- Filter rows where status == "todo" ✓
- Raise error if status column missing ✓
- Return list of filtered rows (dicts) ✓
- Ignore rows with status != "todo" (silently skip) ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_request_orchestrator.py::test_filter_* -v  # Phase 5
```

**Test File**: `tests/unit/test_request_orchestrator.py`

**Test Fixtures**:
- Test data: `[{"name": "Alice", "status": "todo"}, {"name": "Bob", "status": "done"}, {"name": "Carol", "status": "todo"}]`

**Test Cases**:
1. `test_filter_returns_only_todo_rows` — Filters 3 rows → 2 "todo" rows returned ✓
2. `test_filter_empty_data_returns_empty` — Empty list → empty list ✓
3. `test_filter_no_todo_rows` — All "done" rows → empty list ✓
4. `test_filter_missing_status_column_raises_error` — KeyError raised ✓
5. `test_filter_preserves_all_columns` — Filtered rows have all original columns ✓

**Expected Output**:
```
tests/unit/test_request_orchestrator.py::test_filter_returns_only_todo_rows PASSED
tests/unit/test_request_orchestrator.py::test_filter_empty_data_returns_empty PASSED
tests/unit/test_request_orchestrator.py::test_filter_no_todo_rows PASSED
tests/unit/test_request_orchestrator.py::test_filter_missing_status_column_raises_error PASSED
tests/unit/test_request_orchestrator.py::test_filter_preserves_all_columns PASSED

======================== 5 passed in 0.06s ========================
```

**Verification**: Filtering logic is correct, edge cases handled.

---

### Task 5.2: Implement DocumentEngine Wrapper
**Status**: `[todo]`

**Description**: Create `src/document_engine.py` wrapper to invoke doc-modification engine for each filtered row.

**Related Requirements**: FR13, FR14, FR15, IR4, IR5, IR6

**Acceptance Criteria**:
- Call document-modification engine with template, data row, output config ✓
- Capture success/failure status per row ✓
- Return GenerationResult with counts and error details ✓
- Preserve fonts and line breaks (via doc-modification engine guarantee) ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_document_engine.py -v
```

**Test File**: `tests/unit/test_document_engine.py`

**Test Fixtures**:
- `tests/fixtures/sample_template.docx` — Tokenized template with {{name}}, {{email}}
- Mock data row: `{"name": "Alice", "email": "alice@example.com"}`

**Test Cases**:
1. `test_invoke_engine_single_row` — Generates 1 document, returns success ✓
2. `test_invoke_engine_multiple_rows` — Generates 2 documents, returns count ✓
3. `test_invoke_engine_invalid_row_data` — Missing field → failure captured ✓
4. `test_invoke_engine_template_not_found` — FileNotFoundError → failure captured ✓
5. `test_invoke_engine_output_formats` — Generates docx + pdf ✓
6. `test_generation_result_includes_error_details` — Failed row info is detailed ✓

**Expected Output**:
```
tests/unit/test_document_engine.py::test_invoke_engine_single_row PASSED
tests/unit/test_document_engine.py::test_invoke_engine_multiple_rows PASSED
tests/unit/test_document_engine.py::test_invoke_engine_invalid_row_data PASSED
tests/unit/test_document_engine.py::test_invoke_engine_template_not_found PASSED
tests/unit/test_document_engine.py::test_invoke_engine_output_formats PASSED
tests/unit/test_document_engine.py::test_generation_result_includes_error_details PASSED

======================== 6 passed in 0.15s ========================
```

**Verification**: Engine invoked correctly, results captured, errors detailed.

---

### Task 5.3: Implement Status Update Logic
**Status**: `[todo]`

**Description**: Add update_status() method to RequestOrchestrator. Update source table with "done" status for successful rows.

**Related Requirements**: FR16, FR17, FR18, FR19, NFR5, NFR6, NFR7

**Acceptance Criteria**:
- Mark successful rows as "done" ✓
- Keep failed rows as "todo" ✓
- Preserve all other column values ✓
- Persist updated file (via FileStorage) ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_request_orchestrator.py::test_update_* -v
```

**Test Cases**:
1. `test_update_status_marks_successful_done` — 2 successful → status = "done" ✓
2. `test_update_status_keeps_failed_todo` — 1 failed → status remains "todo" ✓
3. `test_update_status_preserves_other_columns` — name, email columns unchanged ✓
4. `test_update_status_idempotent` — Rerun filters out "done" rows, only new "todo" processed ✓
5. `test_update_status_saves_to_file` — Updated file written to disk ✓

**Expected Output**:
```
tests/unit/test_request_orchestrator.py::test_update_status_marks_successful_done PASSED
tests/unit/test_request_orchestrator.py::test_update_status_keeps_failed_todo PASSED
tests/unit/test_request_orchestrator.py::test_update_status_preserves_other_columns PASSED
tests/unit/test_request_orchestrator.py::test_update_status_idempotent PASSED
tests/unit/test_request_orchestrator.py::test_update_status_saves_to_file PASSED

======================== 5 passed in 0.10s ========================
```

**Verification**: Status updates work, file persisted, idempotency confirmed.

---

## Phase 6: Additional Slack Integration Features

### Task 6.1: Implement Enhanced Slack Event Listener
**Status**: `[todo]`

**Description**: Create `src/main.py` with Slack Events API listener using slack-bolt.

**Related Requirements**: FR1, FR2, FR3, FR4, IR1, IR2, IR3

**Acceptance Criteria**:
- Listen for `app_mention` events ✓
- Extract context from Slack message (channel ID, config file name) ✓
- Post completion report to originating channel ✓
- Handle malformed requests gracefully ✓

**Test Command**:
```bash
python -m pytest tests/integration/test_slack_event_flow.py -v
```

**Test File**: `tests/integration/test_slack_event_flow.py`

**Test Cases** (mocked Slack API):
1. `test_app_mention_extracted_correctly` — Parses @Claude mention, extracts channel ID ✓
2. `test_config_file_name_extracted` — Detects config file from message context ✓
3. `test_post_completion_success_message` — Posts "X succeeded, Y failed" message ✓
4. `test_post_completion_error_message` — Posts error on config not found ✓
5. `test_malformed_event_handled_gracefully` — Ignores non-mention events ✓

**Expected Output**:
```
tests/integration/test_slack_event_flow.py::test_app_mention_extracted_correctly PASSED
tests/integration/test_slack_event_flow.py::test_config_file_name_extracted PASSED
tests/integration/test_slack_event_flow.py::test_post_completion_success_message PASSED
tests/integration/test_slack_event_flow.py::test_post_completion_error_message PASSED
tests/integration/test_slack_event_flow.py::test_malformed_event_handled_gracefully PASSED

======================== 5 passed in 0.12s ========================
```

**Verification**: Slack events received, context extracted, messages posted.

---

### Task 6.2: Implement Rate Limiting (30s per channel)
**Status**: `[todo]`

**Description**: Add rate limiter to RequestOrchestrator. Enforce 1 request per 30 seconds per Slack channel.

**Related Requirements**: NFR3

**Acceptance Criteria**:
- Track last request timestamp per channel ✓
- Reject requests within 30 seconds ✓
- Post warning to Slack if rate limited ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_request_orchestrator.py::test_rate_* -v
```

**Test Cases**:
1. `test_rate_limit_first_request_allowed` — First request passes ✓
2. `test_rate_limit_second_request_within_30s_denied` — 2nd request at 5s → denied ✓
3. `test_rate_limit_request_after_30s_allowed` — Request at 31s → allowed ✓
4. `test_rate_limit_warning_posted_to_slack` — Rejection message posted ✓

**Expected Output**:
```
tests/unit/test_request_orchestrator.py::test_rate_limit_first_request_allowed PASSED
tests/unit/test_request_orchestrator.py::test_rate_limit_second_request_within_30s_denied PASSED
tests/unit/test_request_orchestrator.py::test_rate_limit_request_after_30s_allowed PASSED
tests/unit/test_request_orchestrator.py::test_rate_limit_warning_posted_to_slack PASSED

======================== 4 passed in 0.08s ========================
```

---

## Phase 7: Result Handler & Reporting

### Task 7.1: Implement ResultHandler
**Status**: `[todo]`

**Description**: Create `src/result_handler.py` to update source table and post Slack report.

**Related Requirements**: FR18, FR23, FR24

**Acceptance Criteria**:
- Save updated source table with status changes ✓
- Post completion report: "X succeeded, Y failed" ✓
- Include error details for failed rows ✓

**Test Command**:
```bash
python -m pytest tests/unit/test_result_handler.py -v
```

**Test File**: `tests/unit/test_result_handler.py`

**Test Cases**:
1. `test_result_handler_formats_success_message` — Message: "2 documents generated" ✓
2. `test_result_handler_formats_partial_failure_message` — Message: "2 succeeded, 1 failed" ✓
3. `test_result_handler_includes_failure_details` — Failed row: Alice (missing email) ✓
4. `test_result_handler_saves_updated_file` — File written with status = "done" ✓

**Expected Output**:
```
tests/unit/test_result_handler.py::test_result_handler_formats_success_message PASSED
tests/unit/test_result_handler.py::test_result_handler_formats_partial_failure_message PASSED
tests/unit/test_result_handler.py::test_result_handler_includes_failure_details PASSED
tests/unit/test_result_handler.py::test_result_handler_saves_updated_file PASSED

======================== 4 passed in 0.08s ========================
```

---

## Phase 8: End-to-End Integration Testing

### Task 8.1: E2E Test: Full Workflow (Happy Path)
**Status**: `[todo]`

**Description**: Full workflow test: Slack mention → config load → filter → generate → update → report.

**Related Requirements**: All FR 1–24, NFR 1–10

**Acceptance Criteria**:
- Slack event received ✓
- Config loaded and validated ✓
- Data filtered by status ✓
- Documents generated ✓
- Status updated in source table ✓
- Completion report posted ✓

**Test Command**:
```bash
python -m pytest tests/integration/test_document_generation_e2e.py::test_e2e_happy_path -v -s
```

**Test File**: `tests/integration/test_document_generation_e2e.py`

**Setup**: Create fixtures:
- `settings/test_config.json` (valid config)
- `data/test_data.xlsx` (3 rows: 2 "todo", 1 "done")
- `templates/test_template.docx` (with {{name}}, {{email}} tokens)
- `output/` directory

**Test Case**:
1. `test_e2e_happy_path`:
   - Simulate Slack mention with config name "test_config"
   - Verify config loads ✓
   - Verify data filtered (2 rows) ✓
   - Verify documents generated (2 files in output/) ✓
   - Verify source table updated (2 rows now "done") ✓
   - Verify Slack message posted: "2 documents generated" ✓

**Expected Output**:
```
tests/integration/test_document_generation_e2e.py::test_e2e_happy_path PASSED

Generated files:
  output/applicant_001.docx
  output/applicant_001.pdf
  output/applicant_003.docx
  output/applicant_003.pdf

Updated source table:
  Row 1: Alice, status=done
  Row 2: Bob, status=done (unchanged)
  Row 3: Carol, status=done

Slack message posted:
  "✓ 2 documents generated (2 formats: docx, pdf)"
```

---

### Task 8.2: E2E Test: Partial Failure
**Status**: `[todo]`

**Description**: Test handling of partial failures (1 invalid row, 1 success).

**Related Requirements**: FR20–FR24, NFR6

**Acceptance Criteria**:
- Invalid row (missing field) fails generation ✓
- Valid row generates successfully ✓
- Invalid row status stays "todo" (resumable) ✓
- Valid row status changes to "done" ✓
- Report shows "1 succeeded, 1 failed" ✓

**Test Command**:
```bash
python -m pytest tests/integration/test_document_generation_e2e.py::test_e2e_partial_failure -v -s
```

**Test Case**:
1. `test_e2e_partial_failure`:
   - Data: 1 valid row (Alice), 1 invalid row (Bob, missing email field)
   - Generate documents
   - Verify output: 1 docx/pdf pair (Alice)
   - Verify source table: Alice="done", Bob="todo"
   - Verify Slack message: "1 succeeded, 1 failed – Bob: missing email"

**Expected Output**:
```
tests/integration/test_document_generation_e2e.py::test_e2e_partial_failure PASSED

Generated files:
  output/applicant_001.docx
  output/applicant_001.pdf

Updated source table:
  Row 1: Alice, status=done
  Row 2: Bob, status=todo (failed)

Slack message posted:
  "⚠️ 1/2 succeeded, 1 failed
   - Bob (row 2): Missing required field 'email'"
```

---

### Task 8.3: E2E Test: Idempotency (Rerun Safety)
**Status**: `[todo]`

**Description**: Verify rerunning on same data only processes new "todo" rows.

**Related Requirements**: NFR5, NFR7

**Acceptance Criteria**:
- First run: generates 2 documents, marks as "done" ✓
- Second run (same data): generates 0 documents (all "done"), no overwrites ✓
- Slack message: "0 documents generated – all rows already done"

**Test Command**:
```bash
python -m pytest tests/integration/test_document_generation_e2e.py::test_e2e_idempotent_rerun -v -s
```

**Test Case**:
1. `test_e2e_idempotent_rerun`:
   - Run 1: 2 "todo" rows → generate, mark "done"
   - Run 2 (immediate): same data → 0 generated (all "done")
   - Verify output/ directory unchanged (no new files)
   - Verify Slack message: "0 documents – all rows already processed"

**Expected Output**:
```
tests/integration/test_document_generation_e2e.py::test_e2e_idempotent_rerun PASSED

Run 1:
  Generated: 2 documents
  Status updates: 2 rows "todo" → "done"

Run 2 (rerun):
  Generated: 0 documents (all rows "done")
  Status updates: 0 rows (no changes)

Slack message Run 2:
  "ℹ️ 0 new documents generated – all 2 rows already processed"
```

---

## Phase 9: Documentation & Cleanup

### Task 9.1: Update README.md
**Status**: `[todo]`

**Description**: Write user-facing README with setup, configuration, and troubleshooting.

**Includes**:
- Installation steps
- Configuration template
- CLI invocation (if applicable)
- Troubleshooting guide
- Example workflow

**Verification**: README is clear and accurate per spec.

---

### Task 9.2: Code Review & Cleanup
**Status**: `[todo]`

**Description**: Review all code for:
- Type hints (mypy clean)
- Docstrings (Google style)
- Error messages (actionable)
- Test coverage (>80%)

**Test Command**:
```bash
mypy src/ --ignore-missing-imports
coverage run -m pytest tests/
coverage report --min-coverage=80
```

**Expected Output**:
```
Success: no issues found in 6 source files

Name                        Stmts   Miss  Cover
──────────────────────────────────────────
src/main.py                  45      2    96%
src/config_manager.py        32      1    97%
src/request_orchestrator.py  68      3    96%
src/document_engine.py       54      2    96%
src/file_storage.py          78      5    94%
src/result_handler.py        40      2    95%
──────────────────────────────────────────
TOTAL                        317     15    95%

======================== COVERAGE OK ========================
```

---

## Summary: Test Execution Order

**Recommended Test Execution Phases**:

1. **Phase 1**: Setup (no tests required, manual verification)
2. **Phase 2**: MVP Integration (run only Phase 2 MVP tests)
   ```bash
   python -m pytest tests/unit/test_slack_listener.py tests/unit/test_cowork_forwarder.py tests/integration/test_mvp_slack_to_cowork.py -v
   ```
   Expected: 16 passed

3. **Phases 3–7**: Full stack tests
   ```bash
   # Unit tests (Phases 3–7)
   python -m pytest tests/unit/ -v
   
   # Integration tests (Phases 8)
   python -m pytest tests/integration/ -v
   
   # Full suite with coverage
   python -m pytest tests/ --cov=src --cov-report=html
   ```

**Expected Final Result** (after all phases complete):
```
======================== 58 passed in 1.45s ========================
Coverage: 95%
```

**MVP Checkpoint**: After Phase 2, the system can receive Slack mentions and forward to Claude Cowork. This is a stable milestone before adding document generation features.

---

## Risk & Mitigation

| Risk | Mitigation |
|------|-----------|
| Google Drive auth failures | Mock API in tests; fallback to local in production |
| Partial file corruption (status update) | Atomic write: write to temp, then rename |
| Concurrent Slack requests | Sequential queue; warn if concurrent ≥2 |
| Performance (100+ rows) | Batch by 50, process asynchronously, set 60s timeout |

---

## Walkthrough / Progress Tracking

As each task completes, update `docs/walkthrough.md` with:
- Date completed
- Test output (paste actual test results)
- Any deviations from plan
- Next milestone

**Critical Milestone**: After Phase 2 (MVP), document the working Slack ↔ Claude Cowork integration before proceeding to document generation features.

Example:
```markdown
## Phase 2.3 — MVP Integration Test
**Status**: ✅ DONE (2026-01-15)

**Evidence**:
```
tests/integration/test_mvp_slack_to_cowork.py::test_mvp_slack_mention_to_cowork_forward PASSED

Logs:
  [INFO] Slack event received: app_mention in channel C01234567890
  [SUCCESS] MVP workflow complete: Slack → Claude Cowork
```

**Notes**: MVP complete! Slack mentions are now forwarded to Claude Cowork. Ready to begin Phase 3.

---

## Phase 5.1 — RequestOrchestrator Status Filtering
**Status**: ✅ DONE (2026-01-20)

**Evidence**:
```
tests/unit/test_request_orchestrator.py::test_filter_returns_only_todo_rows PASSED
... (5 passed in 0.06s)
```

**Notes**: Filter logic handles edge cases correctly. All 5 tests passing.
```

