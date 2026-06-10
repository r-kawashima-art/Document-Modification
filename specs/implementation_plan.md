# Implementation Plan

Aligned with the formal data flow in `design.md §1.1`. Each phase maps to one workflow component or verification checkpoint. Tasks include state tracking (`[todo]`, `[doing]`, `[done]`), deliverables, acceptance criteria, and dependencies.

---

## Phase 0 — Foundation (Completed)

Core engine for document tokenization and rendering. All NFRs met (font preservation, line-break integrity).

| # | Task | Deliverable | [State] | Dependencies |
|---|------|-------------|---------|-------------|
| 0.1 | Project scaffolding (`requirements.txt`, package skeleton) | `/requirements.txt`, `/src/doc_modifier/__init__.py` | [done] | — |
| 0.2 | Implement data loader: `xlsx_loader.load_rows(path) → List[Dict]` | `/src/doc_modifier/xlsx_loader.py` | [done] | 0.1 |
| 0.3 | Implement run-aware token replacer (preserves `<w:rPr>`, line breaks) | `/src/doc_modifier/docx_replacer.py` | [done] | 0.1 |
| 0.4 | Implement Excel cell replacer (openpyxl) | `/src/doc_modifier/xlsx_replacer.py` | [done] | 0.1 |
| 0.5 | Implement PDF exporter with fallback chain (docx2pdf → LibreOffice) | `/src/doc_modifier/pdf_exporter.py` | [done] | 0.1 |
| 0.6 | Implement rendering pipeline orchestrator | `/src/doc_modifier/pipeline.py` | [done] | 0.2–0.5 |
| 0.7 | Implement CLI: `python -m doc_modifier --template … --data … --out …` | `/src/doc_modifier/cli.py` | [done] | 0.6 |
| 0.8 | Unit tests: font/line-break preservation, token matching | `/tests/test_docx_replacer.py` | [done] | 0.3–0.5 |
| 0.9 | Smoke test: render sample data, verify output counts and formatting | `/output/`, `/docs/walkthrough.md` | [done] | 0.6–0.8 |

**End Condition**: CLI renders sample data; output `.docx` and `.pdf` files with unchanged fonts/line breaks. Phase 0 gates all downstream work.

---

## Phase 1 — Data Intake (Design.md Phase 1)

Slack form submission → Google Sheets row creation with unique job ID.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 1.1 | Define Slack request payload schema and webhook endpoint | `/src/doc_modifier/slack_client.py` (docstring + type hints) | [todo] | 0.7 | Payload schema documented; request parsing code accepts `{name, date_of_birth, nationality, passport_no, …}` |
| 1.2 | Implement `slack_client.parse_form(webhook_payload) → Dict` | `/src/doc_modifier/slack_client.py` | [todo] | 1.1 | Parses Slack form payload; returns structured dict with all fields; raises on missing required fields |
| 1.3 | Define job_id generation (UUID4) and job record schema | `/src/doc_modifier/job_store.py` (docstring) | [todo] | 1.1 | Job record: `{job_id, status, name, submission_timestamp, approver_id, …}` |
| 1.4 | Implement `job_store.store_job(job_data) → job_id` | `/src/doc_modifier/job_store.py` | [todo] | 1.3 | Stores job record persistently (JSON/SQLite); returns `job_id`; state = `CAPTURING` |
| 1.5 | Implement `slack_client.append_to_sheets(job_id, form_data)` (via Google Sheets MCP) | `/src/doc_modifier/slack_client.py` | [todo] | 1.2, 1.4 | Appends row to `data/sample_data.xlsx`; row includes `job_id` and all form fields; validates headers match tokens |
| 1.6 | Unit test: parse valid/invalid Slack payloads; store and retrieve jobs | `/tests/test_slack_intake.py` | [todo] | 1.2–1.5 | Valid payload → job stored; invalid → exception raised; retrieved job matches stored data |
| 1.7 | Integration test: Slack webhook → job stored → row in Sheets | `/tests/test_phase1_e2e.py` | [todo] | 1.5, 1.6 | Webhook triggers; row appears in Sheets within 5 seconds; job_id matches row identifier |

**End Condition** (Phase 1 complete): New job record persisted; corresponding row added to Google Sheets; state = `CAPTURING`.

---

## Phase 2 — Approval Gate (Design.md Phase 2)

Slack workflow execution: person in charge approves/rejects request.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 2.1 | Define approval message format (with job_id, applicant name, metadata) | `/src/doc_modifier/slack_client.py` (template in docstring) | [todo] | 1.4 | Message includes `job_id`, `{name}`, submission timestamp; includes approve/reject buttons |
| 2.2 | Implement `slack_client.post_approval_request(job_id, applicant_name)` | `/src/doc_modifier/slack_client.py` | [todo] | 2.1, 1.4 | Posts approval message to Slack channel; message contains job_id; returns message_ts |
| 2.3 | Update job state to `AWAITING_APPROVAL` | `/src/doc_modifier/job_store.py` | [todo] | 1.4 | After approval request posted, update job record: `status = AWAITING_APPROVAL, message_ts = …` |
| 2.4 | Unit test: format and validate approval message structure | `/tests/test_approval_message.py` | [todo] | 2.1 | Message JSON structure valid; includes all required fields; job_id is present and unique |
| 2.5 | Integration test: post approval request and manually approve in Slack | manual | [todo] | 2.2, 2.3 | Approval message appears in Slack; approver can click approve/reject button |

**End Condition** (Phase 2 complete): Approval request posted to Slack; job state = `AWAITING_APPROVAL`; awaiting user action.

---

## Phase 3 — Approval Polling & Persistence (Design.md Phase 3)

Monitor Slack approval channel; detect approval/rejection; persist decision.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 3.1 | Implement approval decision schema (`{job_id, approved: bool, approver_id, timestamp}`) | `/src/doc_modifier/job_store.py` (docstring) | [todo] | 2.3 | Schema defined; can be serialized to JSON |
| 3.2 | Implement `slack_client.poll_approval_channel(timeout_sec) → Dict` | `/src/doc_modifier/slack_client.py` | [todo] | 3.1 | Polls Slack for approval messages; returns decision dict with `{job_id, approved, approver_id}` |
| 3.3 | Implement `job_store.update_decision(job_id, decision)` | `/src/doc_modifier/job_store.py` | [todo] | 3.1, 3.2 | Updates job record: state = `APPROVED` or `REJECTED`; decision metadata persisted; immutable (no overwrites) |
| 3.4 | Implement state transition logic: `AWAITING_APPROVAL` → `APPROVED` | `REJECTED` | `/src/doc_modifier/workflow.py` | [todo] | 3.3 | Workflow checks job state; on approval: transition to `APPROVED`; on rejection: transition to `REJECTED` |
| 3.5 | Unit test: poll approval messages; parse and persist decisions | `/tests/test_approval_polling.py` | [todo] | 3.2, 3.3 | Valid approval message parsed correctly; state transition applied; decision not mutable |
| 3.6 | Integration test: Slack approval → job state updated → decision in job_store | `/tests/test_phase3_e2e.py` | [todo] | 3.4, 3.5 | Click approve in Slack; poll detects within 5 seconds; job state = `APPROVED` in store |

**End Condition** (Phase 3 complete): Approval decision detected and persisted; job state = `APPROVED` or `REJECTED`; audit trail recorded.

---

## Phase 4 — Document Generation (Design.md Phase 4)

Render document from template + approved data row. **Conditional on approval.**

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 4.1 | Implement approval-gate check before generation | `/src/doc_modifier/workflow.py` | [todo] | 3.4 | If `status != APPROVED`, skip phase 4; log decision; return early |
| 4.2 | Implement `workflow.trigger_generation(job_id)` entrypoint | `/src/doc_modifier/workflow.py` | [todo] | 4.1, 0.6 | Fetches job data and approved row from Sheets; invokes `pipeline.run(template, row_data, out_dir)` |
| 4.3 | Implement error handling: token not found, PDF backend missing | `/src/doc_modifier/pipeline.py`, `/src/doc_modifier/pdf_exporter.py` | [todo] | 0.6, 0.8 | Missing token → log warning, continue; PDF export fails → log, keep `.docx`; partial output allowed |
| 4.4 | Update job state: `APPROVED` → `GENERATING` → `DELIVERING_LOCAL` | `/src/doc_modifier/job_store.py` | [todo] | 4.2 | State updated before generation starts; updated again after write to `/output/` |
| 4.5 | Store output filenames in job record | `/src/doc_modifier/job_store.py` | [todo] | 4.4 | Job record updated: `{output_docx_path, output_pdf_path}` (or `null` if export skipped) |
| 4.6 | Unit test: approved job triggers generation; rejected job skips it | `/tests/test_generation_gate.py` | [todo] | 4.1, 4.2 | Approved job → pipeline invoked; rejected job → pipeline skipped; output paths recorded |
| 4.7 | Integration test: Slack approval → document generated → files in `/output/` | `/tests/test_phase4_e2e.py` | [todo] | 4.5, 4.6 | Approval triggers generation; rendered `.docx` in `/output/` within 10 seconds; tokens replaced; fonts/line-breaks preserved |

**End Condition** (Phase 4 complete): Rendered documents created in `/output/`; job state = `DELIVERING_LOCAL`; output paths persisted in job record.

---

## Phase 5 — File Storage & Cloud Sync (Design.md Phase 5)

Upload rendered files to Google Drive; generate shareable links.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 5.1 | Implement `drive_client.upload_file(file_path, folder_id) → {file_id, drive_url}` | `/src/doc_modifier/drive_client.py` | [todo] | 4.5 | Uploads `.docx`/`.pdf` to Google Drive folder; returns `file_id` and shareable URL |
| 5.2 | Implement retry logic with exponential backoff (max 3 attempts, 2s base) | `/src/doc_modifier/drive_client.py` | [todo] | 5.1 | On upload failure: retry up to 3 times with backoff; fail fast after retries exhausted; log each attempt |
| 5.3 | Update job state: `DELIVERING_LOCAL` → `DELIVERING_DRIVE` | `/src/doc_modifier/job_store.py` | [todo] | 5.1 | State updated before upload; updated again after success; state = `FAILED` on final retry failure |
| 5.4 | Store Drive metadata in job record | `/src/doc_modifier/job_store.py` | [todo] | 5.1 | Job record updated: `{drive_file_id, drive_url, upload_timestamp}` |
| 5.5 | Handle partial failure: keep local file if Drive upload fails | `/src/doc_modifier/workflow.py` | [todo] | 5.2, 5.3 | Local files preserved regardless of Drive status; job state = `FAILED` but `/output/` file intact |
| 5.6 | Unit test: upload file to Drive; validate URL; handle failures | `/tests/test_drive_upload.py` | [todo] | 5.1, 5.2 | Valid file uploads; URLs are shareable; network error triggers retry; max retries enforced |
| 5.7 | Integration test: rendered files → uploaded to Drive → Drive URL in job record | `/tests/test_phase5_e2e.py` | [todo] | 5.4, 5.6 | Generation → upload within 15 seconds; Drive file appears in specified folder; job record contains Drive URL |

**End Condition** (Phase 5 complete): Files persisted in Google Drive; shareable links in job record; local files retained; job state = `DELIVERING_DRIVE`.

---

## Phase 6 — Completion Notification (Design.md Phase 6)

Post completion message to Slack intake channel with Drive link. **Conditional on outcome.**

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 6.1 | Define completion message format: success, rejection, failure | `/src/doc_modifier/slack_client.py` (template in docstring) | [todo] | 5.4 | Message template includes: `{status, job_id, applicant_name, drive_url}` (if success); `{approver_name}` (if rejected) |
| 6.2 | Implement `slack_client.post_completion_notice(job_id, outcome, drive_url)` | `/src/doc_modifier/slack_client.py` | [todo] | 6.1, 5.4 | Posts formatted message to intake channel; links to Drive (if available); includes job_id for tracing |
| 6.3 | Handle 3 outcomes: `DONE` (success), `REJECTED`, `FAILED` | `/src/doc_modifier/slack_client.py` | [todo] | 6.2 | Success → "✅ Document ready" + Drive link; Rejection → "❌ Request rejected"; Failure → "⚠️ Generation failed" |
| 6.4 | Retry Slack notification up to 2 times on API failure | `/src/doc_modifier/slack_client.py` | [todo] | 6.2 | On Slack API error: retry up to 2 times; log failures; do NOT fail the entire workflow |
| 6.5 | Update job state: `DELIVERING_DRIVE` → `NOTIFYING` → `DONE` | `/src/doc_modifier/job_store.py` | [todo] | 6.2 | State = `NOTIFYING` before Slack post; state = `DONE` after success; state = `FAILED` if notification fails (but job marked incomplete) |
| 6.6 | Unit test: format notifications for success, rejection, failure | `/tests/test_notification_message.py` | [todo] | 6.1 | All 3 message formats valid JSON; include required fields; URLs properly escaped |
| 6.7 | Integration test: completion notification posted to Slack | `/tests/test_phase6_e2e.py` | [todo] | 6.5, 6.6 | After Drive upload, notification appears in Slack within 5 seconds; message is readable; Drive link works |

**End Condition** (Phase 6 complete): Slack notification posted; job state = `DONE` (success) or `FAILED` (if notification failed but Drive upload succeeded). Full workflow end-to-end closure.

---

## Phase 7 — Rejection Path (Design.md Failure Paths)

Handle rejection at Phase 3: skip generation and Drive sync; send rejection notice.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 7.1 | Implement rejection path: `AWAITING_APPROVAL` → `REJECTED` | `/src/doc_modifier/workflow.py` | [todo] | 3.4, 6.1 | If approval rejected: skip phases 4–5; go directly to phase 6 with outcome = `REJECTED` |
| 7.2 | Implement rejection notification: `slack_client.post_rejection(job_id, approver_name)` | `/src/doc_modifier/slack_client.py` | [todo] | 7.1, 6.1 | Posts rejection message with approver name; includes job_id |
| 7.3 | Update job state: `AWAITING_APPROVAL` → `REJECTED` → `DONE` | `/src/doc_modifier/job_store.py` | [todo] | 7.1, 7.2 | State chain: `AWAITING_APPROVAL` → `REJECTED` → (skip 4–5) → `NOTIFYING` → `DONE` |
| 7.4 | Verify NO local/Drive artifacts created for rejected jobs | `/src/doc_modifier/workflow.py` | [todo] | 7.1 | `/output/` remains empty; no Drive files uploaded; only Slack notification sent |
| 7.5 | Unit test: rejection path; no generation triggered | `/tests/test_rejection_path.py` | [todo] | 7.2, 7.3 | Rejected job → pipeline NOT invoked; no files in `/output/`; rejection notification sent |
| 7.6 | Integration test: approval rejection → Slack notification (no file generation) | `/tests/test_phase7_e2e.py` | [todo] | 7.4, 7.5 | Rejection in Slack → notification appears; `/output/` empty; job_store shows `REJECTED` state |

**End Condition** (Phase 7 complete): Rejection path fully implemented; no artifacts created; user notified immediately.

---

## Phase 8 — Error Recovery & Audit Trail

Comprehensive failure handling and traceability.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 8.1 | Document failure modes and recovery procedures | `/docs/runbook.md` | [todo] | 4.3, 5.2, 5.5, 6.4 | Runbook covers: token missing, PDF export fail, Drive upload fail, Slack notification fail; recovery steps for each |
| 8.2 | Implement audit trail: log all state transitions with timestamp | `/src/doc_modifier/job_store.py` | [todo] | 1.4, 3.3, 4.4, 5.3, 6.5 | Job record includes `audit_log: [{timestamp, state_from, state_to, reason}]` |
| 8.3 | Implement rollback procedure: delete Drive files if notification fails | `/src/doc_modifier/drive_client.py` | [todo] | 5.1, 6.4 | If final Slack notification fails: optionally allow user to rollback Drive upload (keep local files) |
| 8.4 | Unit test: all state transitions logged; audit trail immutable | `/tests/test_audit_trail.py` | [todo] | 8.2 | All transitions recorded; audit log is append-only; no mutations |
| 8.5 | Integration test: failure at each phase; verify state and artifact consistency | `/tests/test_error_scenarios.py` | [todo] | 8.1, 8.3 | Failure at phase 4 → job = `FAILED`, `/output/` partial; phase 5 → local safe, Drive empty; phase 6 → file safe, Slack unnotified |

**End Condition** (Phase 8 complete): Full audit trail; documented recovery procedures; partial failure resilience.

---

## Phase 9 — End-to-End Validation

Complete workflow integration and acceptance testing.

| # | Task | Deliverable | [State] | Dependencies | Acceptance Criteria |
|---|------|-------------|---------|-------------|-------------------|
| 9.1 | Happy path: Slack form → approval → document → Drive → Slack notification | `/tests/test_e2e_happy.py` | [todo] | 1.7, 2.5, 3.6, 4.7, 5.7, 6.7 | Full workflow completes in < 30 seconds; all artifacts created; job state = `DONE` |
| 9.2 | Sad path: Slack form → rejection → Slack notification (no artifacts) | `/tests/test_e2e_rejection.py` | [todo] | 1.7, 2.5, 3.6, 7.6 | Rejection blocks generation; no files in `/output/` or Drive; notification sent within 10 seconds |
| 9.3 | Failure resilience: Drive upload fails → local files safe → eventual retry possible | `/tests/test_e2e_drive_failure.py` | [todo] | 5.2, 5.5 | Drive failure triggered; local `/output/` files intact; job state = `FAILED`; manual retry recovers |
| 9.4 | Slack notification failure: file safe in Drive, manual follow-up required | `/tests/test_e2e_slack_failure.py` | [todo] | 6.4 | Slack API fails after Drive upload; file safe; job marked incomplete; admin can manually notify |
| 9.5 | Load test: 10 concurrent Slack submissions; verify all jobs processed correctly | `/tests/test_load_concurrent.py` | [todo] | 9.1, 9.2 | All 10 jobs queued; no race conditions; each produces correct output; job IDs unique; no file collisions |
| 9.6 | Regression test: NFRs 1–2 (fonts, line breaks) still satisfied after workflow | `/tests/test_nfr_post_workflow.py` | [todo] | 4.7, 0.8 | Rendered documents from workflow have identical fonts/line-breaks as baseline; run XML diff |
| 9.7 | Update walkthrough with full happy-path screenshots and links | `/docs/walkthrough.md` (expanded) | [todo] | 9.1 | Screenshots: Slack form → approval → Drive file → completion notification; all links verified working |

**End Condition** (Phase 9 complete): Workflow fully functional; all acceptance criteria met; production-ready.

---

## Task Dependencies & Critical Path

```
Phase 0 (Foundation) ─┐
                       ├─ Phase 1 (Data Intake) ─┐
                                                   ├─ Phase 2 (Approval Gate) ─┐
                                                                               ├─ Phase 3 (Polling) ─┐
                                                                                                     ├─ Phase 4 (Generation) ─┐
                                                                                                                             ├─ Phase 5 (Drive Sync) ─┐
                                                                                                                                                    ├─ Phase 6 (Notification) ─┐
                                                                                                                                                                                ├─ Phase 9 (E2E Validation)
                                                                                                                                                                    ├─ Phase 7 (Rejection Path) ─┘
                                                                                                                                                    ├─ Phase 8 (Audit/Recovery) ─┘
```

**Critical path**: 0 → 1 → 2 → 3 → 4 → 5 → 6 → 9  (~9 work weeks for phases 1–6, assuming 1 week per phase with testing).

---

## Rollout Strategy

1. **Weeks 1–2**: Phase 1 (Slack intake, job store). Demo: manual Slack form → Sheets row.
2. **Weeks 3–4**: Phase 2–3 (Approval workflow). Demo: Slack approval → state change.
3. **Weeks 5–6**: Phase 4 (Generation gate). Demo: approved job → document rendered.
4. **Weeks 7–8**: Phase 5–6 (Drive sync + notification). Demo: full happy path.
5. **Week 9**: Phase 7–8 (Rejection, error recovery, audit trail).
6. **Week 10**: Phase 9 (E2E validation, load testing, walkthrough).

**Deployment**: After phase 6 complete + phase 9 validation, deploy to production with rollback plan (Phase 8).

---

## Traceability Matrix (Updated from design.md)

| Workflow Phase | Design.md Section | Implementation Phase | Modules | Acceptance Test |
|---|---|---|---|---|
| Data Intake | §1.1, Phase 1 | Phase 1 | `slack_client`, `job_store`, `xlsx_loader` | 1.7 |
| Approval Gate | §1.1, Phase 2 | Phase 2 | `slack_client`, `job_store` | 2.5 |
| Approval Polling | §1.1, Phase 3 | Phase 3 | `slack_client`, `job_store`, `workflow` | 3.6 |
| Document Generation | §1.1, Phase 4 | Phase 4 | `workflow`, `pipeline`, `docx_replacer`, `pdf_exporter` | 4.7 |
| File Storage & Sync | §1.1, Phase 5 | Phase 5 | `drive_client`, `job_store` | 5.7 |
| Completion Notification | §1.1, Phase 6 | Phase 6 | `slack_client`, `job_store` | 6.7 |
| Rejection Path | §1.1, Failure Paths | Phase 7 | `workflow`, `slack_client` | 7.6 |
| Audit & Recovery | §1.1, Failure Paths | Phase 8 | `job_store`, `drive_client` | 8.5 |
| E2E Validation | — | Phase 9 | All modules | 9.1–9.7 |
