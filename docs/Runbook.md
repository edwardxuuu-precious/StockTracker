# StockTracker Runbook

Last updated: `2026-02-11`

## Quick Start

1. Full local stack (Windows): `start-all.cmd` (`start-all.bat` is compatibility wrapper)
2. Backend only: `backend/start-backend.cmd`
3. Frontend only: `frontend/start-frontend.cmd`
4. Scheduler (optional): `backend/start-scheduler.cmd`
5. Docker stack (optional): `docker-compose up --build`

## Environment and Dependency Rebuild

### Backend

```bash
py -3.11 -m venv venv
venv\Scripts\python -m pip install -r backend/requirements.txt
venv\Scripts\python -m pytest backend/tests -q
```

### Frontend

```bash
cd frontend
npm ci
npm run lint
npm run test:unit
npm run build
```

## Frontend `.env` Rule

- Source of truth template: `frontend/.env.example`
- Local runtime file: `frontend/.env` (not committed)
- `frontend/start-frontend.cmd` auto-creates `.env` from `.env.example` when missing.

## Market Data Ingestion

Manual API:
`POST /api/v1/market-data/ingest`

Payload fields:
- `symbols`: list of symbols
- `market`: `CN` or `US`
- `interval`: `1m` or `1d`
- `start` / `end`: ISO datetime (optional)
- `provider`: provider name (optional, e.g. `akshare`)

Scheduler:
- Config file: `backend/config/ingestion_jobs.json` (copy from `backend/config/ingestion_jobs.example.json`)
- Run: `backend/start-scheduler.cmd`

## Knowledge Base

Upload file:
`POST /api/v1/kb/ingest` (multipart form)

Upload text:
`POST /api/v1/kb/ingest-text` (multipart form)

Search:
`POST /api/v1/kb/search` (`mode`: `fts` / `vector` / `hybrid`)

## Agent Workflow

- Generate strategy: `POST /api/v1/agent/strategy/generate`
- Tune strategy: `POST /api/v1/agent/strategy/tune`
- Build backtest report: `POST /api/v1/agent/backtests/{backtest_id}/report`
  - When LLM is unavailable, endpoint returns deterministic fallback with `fallback_used=true` and `fallback_reason`.

Agent LLM reliability env vars:
- `AGENT_LLM_TIMEOUT_SECONDS` (default `90.0`)
- `AGENT_LLM_MAX_RETRIES` (default `3`)
- `AGENT_LLM_RETRY_BASE_SECONDS` (default `1.0`)
- `AGENT_LLM_RETRY_MAX_SECONDS` (default `8.0`)

Agent report telemetry:
- `GET /api/v1/telemetry/agent-report-metrics?window=200`
- Returns `success_rate`, `p95_latency_ms`, `fallback_ratio`, `timeout_rate`.

## Strategy Versions

- List: `GET /api/v1/strategies/{strategy_id}/versions`
- Snapshot: `POST /api/v1/strategies/{strategy_id}/versions`
- Compare: `POST /api/v1/strategies/versions/compare`

## Release Gate and Promotion

- Dev gate: `python backend/scripts/release_gate.py --profile dev`
- Staging gate: `python backend/scripts/release_gate.py --profile staging --skip-docker`
- Prod gate: `python backend/scripts/release_gate.py --profile prod --docker-build`
- Local docs link check: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-doc-links.ps1`
- Local cleanup helper: `scripts/clean-local.cmd` (deep cleanup: `scripts/clean-local.cmd -Deep`)

Related docs:
- `docs/Ops/Release_Governance.md`
- `docs/Ops/KB_Threshold_Change_Template.md`
- `docs/Ops/KB_Weekly_Review_Checklist.md`
- `docs/Ops/KB_Monthly_Checkpoint_Template.md`

## Docs and QA Entry

- Docs root: `docs/README.md`
- QA hub: `docs/QA/README.md`
- Cleanup report: `reports/cleanup/cleanup_report_2026-02-11.md`
