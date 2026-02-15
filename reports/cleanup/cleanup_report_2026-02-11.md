# StockTracker Cleanup Report

Date: `2026-02-11`  
Scope: deep cleanup and documentation reorganization without API behavior changes.

## 1. Baseline Validation (Before Cleanup)

- Backend: `venv\Scripts\python -m pytest backend\tests -q` -> `86 passed`
- Frontend lint: `cd frontend && npm run lint` -> pass
- Frontend unit tests: `cd frontend && npm run test:unit` -> `9 passed`

## 2. Move Map (QA Archive Migration)

Archived destination root:
`archive/obsolete/docs_cleanup_20260211/QA/`

Moved items:

- `docs/QA/Handoff_Prompt_for_Codex_2026-02-11.md`
- `docs/QA/UAT_Handoff_2026-02-11.md`
- `docs/QA/UAT_P0_Fixes_Handoff_2026-02-11.md`
- `docs/QA/UAT_Retest_Plan_2026-02-11.md`
- `docs/QA/UAT_TEMPLATE.md`
- `docs/QA/obsolete/` (entire folder)

## 3. Broken-Link Fixes

Fixed references and entries:

- Updated docs root entry to use active QA hub:
  - `docs/README.md`
- Rebuilt runbook references and Ops links:
  - `docs/Runbook.md`
- Updated progress workflow QA log reference:
  - `docs/Progress/Update_Workflow.md`
- Rewrote handoff pointers to current valid paths:
  - `docs/HANDOFF_TO_CODEX_2026-02-10.md`
- Fixed archived retest plan path in active QA execution log:
  - `docs/QA/UAT_Execution_Log_2026-02-11.md`

Link check script:
- `scripts/check-doc-links.ps1`
- Latest result: `OK. Checked 16 markdown files.`

## 4. Script Standardization

Primary Windows startup entrypoint now:

- `start-all.cmd`

Compatibility wrapper retained:

- `start-all.bat` -> delegates to `start-all.cmd`

New maintenance scripts:

- `scripts/clean-local.ps1`
- `scripts/clean-local.cmd`
- `scripts/check-doc-links.ps1`

Server management doc normalized (UTF-8 and actual commands):

- `backend/SERVER_MANAGEMENT.md`

## 5. CI and Policy Changes

Updated:

- `.github/workflows/ci.yml`
  - frontend install changed from `npm install` to `npm ci`
  - added `docs-link-check` job running `scripts/check-doc-links.ps1`

Repository hygiene updates:

- `.gitignore`
  - added `backend/.server_*.pid`, `.mypy_cache/`, `.ruff_cache/`, `.vite/`

## 6. Codebase Cleanup (No API Change)

- Removed unimplemented placeholder routers:
  - `backend/app/api/v1/realtime.py`
  - `backend/app/api/v1/stock.py`
- Removed stale commented router placeholders in:
  - `backend/app/main.py`

## 7. Post-Cleanup Validation

Executed after cleanup:

- Docs integrity: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-doc-links.ps1` -> pass
- Backend: `venv\Scripts\python -m pytest backend\tests -q` -> pass
- Frontend lint: `cd frontend && npm run lint` -> pass
- Frontend unit tests: `cd frontend && npm run test:unit` -> pass
- Frontend build: `cd frontend && npm run build` -> pass

## 8. Notes

- Existing user in-progress code changes were preserved and not reverted.
- Cleanup focused on maintainability, structure, and consistency without changing external API contracts.
