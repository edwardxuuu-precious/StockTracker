# StockTracker Runbook

Last updated: `2026-02-09`

## Quick Start

1. Backend: `backend/start-backend.cmd`
2. Frontend: `frontend/start-frontend.cmd`
3. Scheduler (optional): `backend/start-scheduler.cmd`
4. Docker stack (optional): `docker-compose up --build`

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
Config file: `backend/config/ingestion_jobs.json` (copy from `backend/config/ingestion_jobs.example.json`)
Run: `backend/start-scheduler.cmd`

Scheduler observability (env vars):
- `SCHEDULER_HEARTBEAT_PATH`: heartbeat JSON path (default `.runtime/scheduler/heartbeat.json`)
- `SCHEDULER_REPORT_DIR`: per-cycle report directory (default `.runtime/scheduler/reports`)
- `SCHEDULER_REPORT_RETENTION_COUNT`: keep latest N cycle reports (default `200`)
- `SCHEDULER_ALERT_WEBHOOK`: optional webhook URL for failed cycles
- `SCHEDULER_RUN_ONCE=true`: run one cycle then exit
- `SCHEDULER_POLL_SECONDS`: scheduler loop sleep seconds (default `30`)

## Knowledge Base

Upload file:
`POST /api/v1/kb/ingest` (multipart form)
Fields: `file`, optional `title`, `source_type`

Upload text:
`POST /api/v1/kb/ingest-text` (multipart form)
Fields: `source_name`, `content`

Search:
`POST /api/v1/kb/search`
Payload: `query`, `top_k`, `mode` (`fts` / `vector` / `hybrid`)

## Agent Workflow

Generate strategy from prompt:
`POST /api/v1/agent/strategy/generate`

Tune strategy:
`POST /api/v1/agent/strategy/tune`

Build backtest report:
`POST /api/v1/agent/backtests/{backtest_id}/report`

Chat session:
`POST /api/v1/chat/sessions`
`POST /api/v1/chat/sessions/{session_id}/messages`

## Strategy Versions

List versions:
`GET /api/v1/strategies/{strategy_id}/versions`

Create snapshot:
`POST /api/v1/strategies/{strategy_id}/versions`

Compare versions:
`POST /api/v1/strategies/versions/compare`

## Release Gate and Promotion

Local gate command:
`python backend/scripts/release_gate.py --profile dev`

Staging gate (no image build):
`python backend/scripts/release_gate.py --profile staging --skip-docker`

Prod gate (with image build):
`python backend/scripts/release_gate.py --profile prod --docker-build`

Prod gate with KB policy defaults:
`python backend/scripts/release_gate.py --profile prod --kb-policy backend/config/kb_benchmark_policy.json`

KB benchmark monitor:
`python backend/scripts/kb_benchmark_monitor.py --profile prod`

Windows monitor shortcut:
`backend/kb-monitor.cmd --profile prod`

KB weekly review:
`python backend/scripts/kb_benchmark_review.py --profile prod --lookback 4`

Windows review shortcut:
`backend/kb-review.cmd --profile prod --lookback 4`

KB monthly checkpoint:
`python backend/scripts/kb_benchmark_monthly_checkpoint.py --profile prod --month 2026-02`

Windows monthly shortcut:
`backend/kb-monthly-checkpoint.cmd --profile prod --month 2026-02`

Windows shortcut:
`backend/release-gate.cmd --profile staging --skip-docker`

Deploy with rollback:
`python backend/scripts/deploy_with_rollback.py --env staging --rollback-on-failure`

Deploy dry-run:
`python backend/scripts/deploy_with_rollback.py --env staging --dry-run`

Windows deploy shortcut:
`backend/deploy-with-rollback.cmd --env staging --rollback-on-failure`

Rollback drill:
`python backend/scripts/rollback_drill.py --env staging`

Windows drill shortcut:
`backend/rollback-drill.cmd --env staging`

Details:
`docs/Ops/Release_Governance.md`
`docs/Ops/KB_Threshold_Change_Template.md`
`docs/Ops/KB_Weekly_Review_Checklist.md`
`docs/Ops/KB_Monthly_Checkpoint_Template.md`
