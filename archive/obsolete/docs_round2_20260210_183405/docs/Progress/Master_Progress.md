# StockTracker Master Progress

Last updated: `2026-02-09`

## Overall

- Current phase: `Phase 2 re-scope: local data layer + self-built backtest`
- Delivery confidence: `high` for BL-002 ~ BL-007 scope
- Current backlog file: `docs/Progress/Current_Backlog_2026-02-09.md`
- Progress update workflow: `docs/Progress/Update_Workflow.md`

## Goal Status

| Goal | Status | Notes |
| --- | --- | --- |
| Goal#1 Infrastructure | DONE | Startup scripts, env checks, local workflow stable |
| Goal#2 Portfolio Management | DONE | CRUD + status + filtering + validation delivered |
| Goal#3 Holdings & Trades | DONE (MVP) | Buy/Sell semantics and merged holdings behavior validated |
| Goal#4 Market Data | DONE (MVP) | Local data storage + query/ingest/status + provider abstraction delivered |
| Goal#5 Analytics | DONE (MVP) | Dashboard + CSV exports delivered (needs local-data integration later) |
| Goal#6 Backtest | DONE (MVP) | Local-data backtest engine, trade details, and reproducible results delivered |
| Goal#7 AI Assistant | DONE (MVP) | Agent generate/tune/report + chat + KB citation workflow delivered |
| Goal#8 DevOps/Deploy | DONE (Baseline) | Dockerfiles + compose + CI workflow delivered |

## Completed and Verified in UAT

Note: Prior UAT scope is superseded by the new local-data/backtest requirements.

- BL-002 API de-dup and holdings regression
- BL-003 baseline tests (backend/frontend/lint/build)
- BL-004 trade semantics and PnL math
- BL-005 quotes + cache behavior
- BL-006 analytics dashboard and CSV exports
- BL-007 strategy backtest workflow
- GATE-01 / GATE-02 / GATE-03 regression passes

Reference: `docs/QA/UAT_BL-002_to_BL-007.md`

## Recent Hardening (2026-02-09)

- Security baseline:
  - CORS switched from wildcard to configured origins
  - request body logging removed from middleware
  - non-dev default `SECRET_KEY` startup guard added
  - telemetry logs reduced to sanitized fields
- Dependency security:
  - upgraded `python-multipart` to `0.0.22`
  - removed unused `python-jose` dependency
  - `pip-audit -r backend/requirements.txt` clean
  - `npm audit --omit=dev` clean

## Current Risks
- US free data source is yfinance-based and may have minute-level historical limits.
- Knowledge base retrieval governance now has monthly checkpoint baseline (KB-007), but quarter-level operational evidence is still accumulating.
- Future external display will require data licensing review.
- Deployment/rollback automation is delivered for docker-compose baseline, but cloud deployment endpoints are still pending.
- Scheduler observability is in place (heartbeat/cycle report/webhook), but alert routing policy and SLO thresholds still need tuning.


## Next Focus
1. Add cloud deployment endpoint integration (OPS-003).
2. Operate KB-008 quarter-level KB governance audit based on monthly checkpoints.
3. Tune scheduler alert routing policy and operational SLO thresholds.

## Latest Implementation Notes (2026-02-09)

- Local market data schema + read-only API endpoints added.
- Manual ingestion CLI + AKShare adapter in progress.
- Simulated backtest endpoint disabled pending local-data engine.
- Data health + ingestion log API endpoints added (UI page added).
- Local-data backtest engine wired to Bar1m/Bar1d (validation pending).
- Knowledge base ingestion + hybrid search endpoints added (UI page added).
- Manual ingestion API + scheduler script added (needs job config).
- Scheduler default config path fixed and scheduler tests added.
- US provider switched from placeholder to yfinance adapter.
- Agent workflow added: prompt-to-strategy, tuning, and report endpoints with UI.
- Strategy version snapshots and version comparison APIs/UI added.
- Docker and GitHub Actions CI baseline added.
- KB upload bug fixed (`ingest_file` argument mismatch) and report citation chain validated.
- Added regression tests for market-data ingest endpoint, scheduler idempotence, KB modes/doc list, and backtest trade detail invariants.
- Fixed startup script reliability for cross-directory execution:
  - `backend/start-backend.cmd` now invokes `backend/start_server.py` via absolute script path.
  - `frontend/start-frontend.cmd` now enforces its own working directory.
  - `backend/start-scheduler.cmd` now prefers project venv Python.
- Knowledge-base quality hardening v1:
  - Hybrid search rerank now blends vector/fts/term-overlap/freshness signals.
  - Citation governance now applies score threshold + per-document cap + fallback selection flags.
  - Search/agent citations include confidence, reference_id, governance flags, and targeted snippets.
- Knowledge-base quality hardening v2:
  - Governance/search controls are now configurable via settings and request-level overrides.
  - Source allowlist/block-keyword filters and source-type preference are wired into KB search and agent report citations.
  - Regression coverage added for source policy filters, fallback disable mode, and agent citation request overrides.
- Knowledge-base quality hardening v3:
  - Governance policy profiles (`strict`/`balanced`/`recall`) added and wired to KB search + agent report citations.
  - Retrieval benchmark runner added: `backend/scripts/kb_benchmark.py` with sample cases in `backend/config/kb_benchmark_cases.sample.json`.
  - FTS sanitizer fixed to handle punctuation/hyphenated natural-language queries.
- Backtest metric calibration hardening:
  - Extracted unified metric computation for total_return/sharpe/max_drawdown/win_rate.
  - Fixed terminal equity consistency after forced liquidation.
  - Added regression coverage for bull/bear/choppy/flat regimes and US/CN cross-market execution.
- Release governance baseline:
  - Added profile-based release gate runner: `backend/scripts/release_gate.py`.
  - Added Windows shortcut: `backend/release-gate.cmd`.
  - Added CI promotion workflow: `.github/workflows/promotion-gate.yml`.
  - Added governance runbook: `docs/Ops/Release_Governance.md`.
- Deployment and rollback automation baseline:
  - Added deployment script: `backend/scripts/deploy_with_rollback.py`.
  - Added Windows shortcut: `backend/deploy-with-rollback.cmd`.
  - Promotion workflow now supports post-gate deploy and optional rollback on failure.
  - Deploy report artifacts are generated for audit (`.runtime/deploy_report_*.json`).
- Release gate quality threshold integration:
  - Added KB benchmark threshold checks to release gate with profile-aware modes (`auto/off/optional/required`).
  - Promotion workflow now exposes KB threshold parameters for manual promotions.
  - Added expanded prod benchmark cases (`backend/config/kb_benchmark_cases.prod.json`) and raised default thresholds to `0.45/0.45`.
- KB benchmark reproducibility hardening:
  - Benchmark now runs on isolated benchmark DB with corpus seeding (`backend/config/kb_benchmark_corpus/`).
  - Release gate executes benchmark with `--reset-db` to avoid drift from runtime knowledge-base state.
  - Prod release-gate check passes with default thresholds (`precision>=0.45`, `recall>=0.45`) on curated corpus.
- KB-004 benchmark scale-up and threshold hardening:
  - Added mixed-type corpus pack (`pdf`/`txt`/`json`) in `backend/config/kb_benchmark_corpus/corpus_pack.json`.
  - Added KB-004 cases in `backend/config/kb_benchmark_cases.kb004.json` and profile policy in `backend/config/kb_benchmark_policy.json`.
  - Release gate now supports policy-driven KB mode/cases/threshold resolution via `--kb-policy`.
  - KB-004 benchmark metrics: `seeded_documents=28`, `avg_precision_at_k=0.625`, `avg_keyword_recall=1.0`.
- KB-005 drift monitoring and threshold governance:
  - Added monitor runner `backend/scripts/kb_benchmark_monitor.py` and Windows shortcut `backend/kb-monitor.cmd`.
  - Added weekly monitor workflow `.github/workflows/kb-benchmark-monitor.yml` with artifact upload.
  - Monitor reports are archived under `.runtime/kb_benchmark_history/<profile>/` with retention controls.
  - Threshold change governance template added: `docs/Ops/KB_Threshold_Change_Template.md`.
- KB-006 weekly review cadence and first decision record:
  - Added weekly review runner `backend/scripts/kb_benchmark_review.py` and Windows shortcut `backend/kb-review.cmd`.
  - Added weekly review workflow `.github/workflows/kb-weekly-review.yml`.
  - Added weekly checklist `docs/Ops/KB_Weekly_Review_Checklist.md`.
  - Generated first 4-point prod trend review `.runtime/kb_benchmark_reviews/prod/review_20260209T112145Z.json`.
  - Documented first threshold decision record `docs/Ops/KB_Threshold_Changes/KB-TC-20260209-01.md` (decision: keep thresholds).
- KB-007 monthly checkpoint baseline:
  - Added monthly checkpoint runner `backend/scripts/kb_benchmark_monthly_checkpoint.py` and Windows shortcut `backend/kb-monthly-checkpoint.cmd`.
  - Added monthly checkpoint workflow `.github/workflows/kb-monthly-checkpoint.yml`.
  - Added month-end template `docs/Ops/KB_Monthly_Checkpoint_Template.md`.
  - Generated first month-end report `.runtime/kb_monthly_checkpoints/prod/monthly_2026-02.json`.
  - Documented first month-end governance record `docs/Ops/KB_Monthly_Checkpoints/2026-02_prod.md`.
- Scheduler observability and alerting hardening:
  - Scheduler now writes heartbeat status to `.runtime/scheduler/heartbeat.json`.
  - Scheduler now writes per-cycle execution reports to `.runtime/scheduler/reports/cycle_*.json` with retention cleanup.
  - Optional failure alert hook added via `SCHEDULER_ALERT_WEBHOOK`.
- Rollback drill automation hardening:
  - Added drill runner `backend/scripts/rollback_drill.py` and Windows shortcut `backend/rollback-drill.cmd`.
  - Added monthly drill workflow `.github/workflows/rollback-drill.yml` with archived drill report artifacts.
  - At least one successful local staged drill report generated under `.runtime/rollback_drills/`.
  - Fixed drill retention ordering bug so summary/deploy reports both respect `--retain-count`.
- Ops focused acceptance execution:
  - Added UAT record `docs/QA/UAT_OPS_001_004_2026-02-09.md` with command/evidence/results.
  - Scheduler run-once acceptance evidence captured under `.runtime/uat/` heartbeat and cycle report files.
  - Backend regression baseline updated to `61 passed`.
- Deprecation migration cleanup:
  - Replaced Pydantic class-based `Config` with `ConfigDict/SettingsConfigDict`.
  - Replaced `sqlalchemy.ext.declarative.declarative_base` with `sqlalchemy.orm.declarative_base`.
  - Replaced FastAPI `@app.on_event("startup")` with lifespan startup hook.
  - Backend test suite now runs cleanly with no deprecation warnings in test output.
- Full-chain UAT closeout:
  - Executed `docs/QA/UAT_FullChain_Checklist_2026-02-09.md` end-to-end.
  - Final run status reached `34 PASS / 0 FAIL / 0 BLOCKED` after retest.
  - Initial report API `500` instability was hardened by safe request logging fallback in `backend/app/main.py`.
  - Added regression guard for logging sink failure: `backend/tests/test_main_logging.py`.
  - Backend regression baseline updated to `62 passed`.

