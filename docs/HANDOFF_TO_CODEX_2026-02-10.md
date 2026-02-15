# StockTracker Handoff to Codex

Last updated: `2026-02-11`

## Snapshot

- Branch: `main`
- Working tree: dirty (active backend/API/test/doc changes in progress)
- Current focus: deep cleanup and repository organization without API behavior changes

## Current Validation Baseline

Executed on `2026-02-11`:

- Backend tests: `venv\Scripts\python -m pytest backend\tests -q` -> `86 passed`
- Frontend lint: `cd frontend && npm run lint` -> pass
- Frontend unit tests: `cd frontend && npm run test:unit` -> `9 passed`

## Active Documentation Entry Points

- Docs root: `docs/README.md`
- Runbook: `docs/Runbook.md`
- Progress hub: `docs/Progress/README.md`
- Current backlog: `docs/Progress/Current_Backlog_2026-02-09.md`
- QA hub: `docs/QA/README.md`
- Ops governance: `docs/Ops/Release_Governance.md`

## Operational Entrypoints

- Full stack (Windows): `start-all.cmd`
- Compatibility wrapper: `start-all.bat`
- Backend: `backend/start-backend.cmd`
- Frontend: `frontend/start-frontend.cmd`
- Scheduler: `backend/start-scheduler.cmd`

## Cleanup Assets

- Local cleanup scripts:
  - `scripts/clean-local.ps1`
  - `scripts/clean-local.cmd`
- Docs link checker:
  - `scripts/check-doc-links.ps1`
- Cleanup report:
  - `reports/cleanup/cleanup_report_2026-02-11.md`

## Notes

- Historical QA and handoff materials are archived under:
  - `archive/obsolete/docs_cleanup_20260211/QA/`
- This handoff file is a current-state pointer and should stay concise.
