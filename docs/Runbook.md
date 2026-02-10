# StockTracker Runbook

Last updated: `2026-02-10`

## Quick Start

1. Backend: `backend/start-backend.cmd`
2. Frontend: `frontend/start-frontend.cmd`
3. Scheduler (optional): `backend/start-scheduler.cmd`
4. Docker stack (optional): `docker-compose up --build`

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

## Strategy Versions

- List: `GET /api/v1/strategies/{strategy_id}/versions`
- Snapshot: `POST /api/v1/strategies/{strategy_id}/versions`
- Compare: `POST /api/v1/strategies/versions/compare`

## Release Gate and Promotion

- Dev gate: `python backend/scripts/release_gate.py --profile dev`
- Staging gate: `python backend/scripts/release_gate.py --profile staging --skip-docker`
- Prod gate: `python backend/scripts/release_gate.py --profile prod --docker-build`

Related docs:
- `docs/Ops/Release_Governance.md`
- `docs/Ops/KB_Threshold_Change_Template.md`
- `docs/Ops/KB_Weekly_Review_Checklist.md`
- `docs/Ops/KB_Monthly_Checkpoint_Template.md`

## Evidence Location Note

Historical `.runtime` evidence was archived during cleanup.

Primary archive roots:
- `archive/generated/cleanup_20260210_173315/`
- `archive/obsolete/docs_round2_20260210_183405/`
- `archive/obsolete/docs_round3_20260210_204843/`
