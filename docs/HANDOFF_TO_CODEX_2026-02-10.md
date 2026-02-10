# StockTracker Handoff to Codex

Last updated: `2026-02-10`

## Snapshot

- Branch: `main`
- Last baseline commit before this doc refresh: `dc95248`
- Core status: backend tests passing, frontend lint/unit/build passing, repository cleanup round 1-3 completed.

## Current Repository State

### Code and Test Status

- Backend test suite: `79 passed`
- Frontend unit tests: pass (`npm run test:unit`)
- Frontend lint: pass (`npm run lint`)
- Frontend build: pass (`npm run build`, requires `.env`)
- Dependency checks:
  - Python: `pip check` passed
  - Node: installed via `npm ci`

### Cleanup and Restructure Status

Completed on `2026-02-10`:

1. Runtime/cache cleanup
- Removed transient caches and stale runtime artifacts.
- Archived runtime evidence under:
  - `archive/generated/cleanup_20260210_173315/`

2. Documentation cleanup (round 2)
- Consolidated active docs in `docs/Progress` and `docs/QA`.
- Archived historical docs under:
  - `archive/obsolete/docs_round2_20260210_183405/`

3. Active-doc minimization (round 3)
- Reduced active QA milestone summaries to one overview entry.
- Archived detailed QA milestone docs under:
  - `archive/obsolete/docs_round3_20260210_204843/`

4. Dependency-layer slimming
- Removed and rebuilt `venv/`.
- Removed and rebuilt `frontend/node_modules/`.
- Removed root-level redundant `package-lock.json`.

5. Windows reserved-path artifacts
- Removed accidental `NUL` / `backend/NUL` entries.

6. Frontend env template convergence
- Keep template in `frontend/.env.example`.
- `.env` is local-only, auto-created by `frontend/start-frontend.cmd` when missing.

## Active Documentation Entry Points

- Progress hub: `docs/Progress/README.md`
- Current backlog: `docs/Progress/Current_Backlog_2026-02-09.md`
- Update workflow: `docs/Progress/Update_Workflow.md`
- QA hub: `docs/QA/README.md`
- Real usage log: `docs/QA/UAT_RealUsage_Log_2026-02.md`
- AI quality overview: `docs/QA/AI_Quality_Overview_2026-02-10.md`
- Operations runbook: `docs/Runbook.md`
- Docs root entry: `docs/README.md`

## Evidence and Reports

- Cleanup reports:
  - `reports/cleanup/cleanup-report.md`
  - `reports/cleanup/post_round3/cleanup-report.md`
  - `reports/cleanup/post_min_docs/cleanup-report.md`
  - `reports/cleanup/post_audit2/cleanup-report.md`
- Cleanup action logs:
  - `reports/cleanup/cleanup_actions_20260210_173315.md`
  - `reports/cleanup/docs_round2_actions_20260210_183405.md`
  - `reports/cleanup/docs_round3_actions_20260210_204843.md`

## Known Gaps

1. Frontend dependency security
- `npm audit` reports one high vulnerability on `axios` (`<=1.13.4`) with fix available.

2. Product roadmap items still pending
- `OPS-003`: cloud promotion endpoint integration.
- `KB-008`: quarterly governance audit mechanism.

## Resume Checklist

1. Confirm environment
- Backend: `venv/Scripts/python -m pytest backend/tests -q`
- Frontend: `cd frontend && npm run lint && npm run test:unit`

2. Read in order
- `docs/HANDOFF_TO_CODEX_2026-02-10.md`
- `docs/Progress/Current_Backlog_2026-02-09.md`
- `docs/QA/UAT_RealUsage_Log_2026-02.md`

3. Execute top-priority active task from backlog.
