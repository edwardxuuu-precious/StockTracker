# StockTracker Acceptance Checklist (2026-02-09)

Use this checklist for step-by-step acceptance across backend, frontend, scheduling, and knowledge base.

Latest focused UAT report:
- `docs/QA/UAT_OPS_001_004_2026-02-09.md`
- `docs/QA/UAT_KB_004_2026-02-09.md`
- `docs/QA/UAT_KB_005_2026-02-09.md`
- `docs/QA/UAT_KB_006_2026-02-09.md`
- `docs/QA/UAT_KB_007_2026-02-09.md`

Master end-to-end UAT checklist template for upcoming user-side validation:
- `docs/QA/UAT_FullChain_Checklist_2026-02-09.md`
- `docs/QA/UAT_FullChain_Execution_2026-02-09.md`
- `docs/QA/UAT_FullChain_Defects_2026-02-09.md`
- `docs/QA/UAT_RealUsage_Log_2026-02.md`

## Automated Verification Snapshot (2026-02-09)

- Backend tests: `python -m pytest backend/tests -q` -> `62 passed`.
- Frontend lint: `npm run lint` -> passed.
- Frontend build: `npm run build` -> passed (with backend reachable at `http://localhost:8001`).
- Backend deprecation warnings (Pydantic/SQLAlchemy/FastAPI startup) -> cleared in current test output.

## A. Environment and Startup

- [x] `backend/start-backend.cmd` starts successfully and `/docs` is accessible.
- [x] `frontend/start-frontend.cmd` starts successfully and main pages are reachable.
- [x] `backend/start-scheduler.cmd` starts successfully with a valid `backend/config/ingestion_jobs.json`.

## B. Market Data Foundation

- [x] `GET /api/v1/market-data/instruments` returns local instruments.
- [x] `GET /api/v1/market-data/bars` returns local `1m` or `1d` bars for a valid symbol.
- [x] `POST /api/v1/market-data/ingest` runs and writes ingestion logs.
- [x] `GET /api/v1/market-data/status` returns total bars, range, and gap estimate.
- [x] `GET /api/v1/market-data/ingestions` shows recent ingestion status.

## C. Backtest Engine (Local Data Only)

- [x] `POST /api/v1/backtests/` runs with local bars and returns `201`.
- [x] Returned backtest has `status=completed` and non-empty metrics.
- [x] `GET /api/v1/backtests/{id}` includes trades and equity curve.
- [x] Trades created by backtest are marked with `is_simulated=false`.
- [x] Performance metric calibration baseline exists for bull/bear/choppy/flat regimes.
- [x] Backtest `final_value` is consistent with terminal `equity_curve` value after forced liquidation.
- [x] Cross-market (US/CN) mapping works in one run using per-symbol market parameters.

## D. Frontend Pages

- [x] `Market Data` page can query data status.
- [x] `Market Data` page can trigger ingestion and show logs.
- [x] `Strategies` page can run backtest and display trade details.
- [x] `Agent` page supports chat, prompt-based strategy generation, tuning, and report display.
- [x] `Knowledge Base` page can upload files and ingest text.
- [x] `Knowledge Base` page can search and display matched chunks.
- [x] `Strategy Versions` page can create snapshots and compare selected versions.

## E. Scheduler

- [x] Scheduler reads jobs from `backend/config/ingestion_jobs.json`.
- [x] At least one configured job is executed and creates ingestion logs.
- [x] Restarting scheduler does not break idempotent ingestion behavior.
- [x] Scheduler writes heartbeat JSON and per-cycle reports under `.runtime/scheduler/`.
- [x] Scheduler supports failure alert webhook hook via `SCHEDULER_ALERT_WEBHOOK`.

## F. Knowledge Base MVP

- [x] PDF/TXT/JSON ingestion works with `POST /api/v1/kb/ingest`.
- [x] Text ingestion works with `POST /api/v1/kb/ingest-text`.
- [x] Search works with `POST /api/v1/kb/search` in `fts`, `vector`, and `hybrid` modes.
- [x] `GET /api/v1/kb/documents` lists ingested documents.
- [x] Search governance supports request-level score/doc-cap/fallback controls.
- [x] Search governance supports source allowlist/block keywords.
- [x] Agent report citations support request-level governance/source filters.
- [x] Search/agent support governance policy profiles (`strict`/`balanced`/`recall`).
- [x] Retrieval benchmark runner is available via `python backend/scripts/kb_benchmark.py --cases <file>`.
- [x] FTS query sanitizer handles punctuation/hyphenated natural-language queries.
- [x] KB-004 corpus pack (mixed `pdf/txt/json` source types) is seeded via `backend/config/kb_benchmark_corpus/corpus_pack.json`.
- [x] Profile-based KB benchmark policy is configured in `backend/config/kb_benchmark_policy.json` and enforced by release gate.
- [x] KB monitor script archives trend reports under `.runtime/kb_benchmark_history/<profile>/`.
- [x] KB monitor retention policy keeps latest N `benchmark_*.json` and `monitor_*.json`.
- [x] Weekly KB monitor workflow `.github/workflows/kb-benchmark-monitor.yml` is in place.
- [x] Threshold changes require evidence template `docs/Ops/KB_Threshold_Change_Template.md`.
- [x] Weekly KB review report script generates trend decision under `.runtime/kb_benchmark_reviews/<profile>/`.
- [x] Weekly KB review workflow `.github/workflows/kb-weekly-review.yml` is in place.
- [x] First threshold decision record is documented in `docs/Ops/KB_Threshold_Changes/`.
- [x] Monthly KB checkpoint script generates month summary under `.runtime/kb_monthly_checkpoints/<profile>/`.
- [x] Monthly KB checkpoint workflow `.github/workflows/kb-monthly-checkpoint.yml` is in place.
- [x] First month-end governance record is documented in `docs/Ops/KB_Monthly_Checkpoints/`.

## G. Regression and Tests

- [x] `python -m pytest backend/tests/test_scheduler.py -q` passes.
- [x] `python -m pytest backend/tests/test_market_data_api.py -q` passes.
- [x] `python -m pytest backend/tests/test_strategy_backtest_api.py -q` passes.

## H. Release Governance

- [x] `backend/scripts/release_gate.py` runs profile-based gates for `dev` / `staging` / `prod`.
- [x] release gate supports `--kb-policy` profile-based KB mode/cases/threshold resolution.
- [x] release gate writes a JSON report into `.runtime/`.
- [x] `.github/workflows/promotion-gate.yml` supports manual promotion gate runs.
- [x] promotion gate uploads report artifact for audit.
- [x] `backend/scripts/deploy_with_rollback.py` performs deploy + health checks + optional rollback.
- [x] deploy flow writes JSON deploy report into `.runtime/`.
- [x] `backend/scripts/rollback_drill.py` runs rollback rehearsal and archives reports in `.runtime/rollback_drills/`.
- [x] rollback drill workflow `.github/workflows/rollback-drill.yml` provides monthly scheduled rehearsal.
- [x] KB benchmark threshold gate is integrated into release gate (`auto/off/optional/required`).
- [x] Prod benchmark corpus and policy thresholds (`0.55/0.80`) can pass via release gate with isolated benchmark DB.

## I. Known Gaps (Not Blocking This Round)

- [ ] Knowledge base quality rerank and citation governance are production-ready at scale (KB-007 monthly governance baseline delivered; longer-term operations evidence accumulation pending).
- [x] Backtest metric calibration is validated across diversified market regimes.
- [ ] Cloud/environment deployment endpoints are fully operationalized.
