# Release Governance

Last updated: `2026-02-09`

## Objective

Provide reproducible promotion gates for `dev` -> `staging` -> `prod` with machine-readable reports.

## Gate Runner

Command:

```bash
python backend/scripts/release_gate.py --profile dev
python backend/scripts/release_gate.py --profile staging --skip-docker
python backend/scripts/release_gate.py --profile prod --docker-build
python backend/scripts/release_gate.py --profile prod --kb-policy backend/config/kb_benchmark_policy.json
python backend/scripts/release_gate.py --profile prod --kb-benchmark-mode required --kb-cases backend/config/kb_benchmark_cases.kb004.json --kb-min-precision 0.55 --kb-min-recall 0.80
```

Windows shortcut:

```bat
backend\release-gate.cmd --profile staging --skip-docker
```

Output:
- JSON report written to `.runtime/release_gate_<profile>_<timestamp>.json`
- Non-zero exit code when any gate fails

## Policy by Profile

`dev`
- required files exist
- env policy (`ALLOW_SIM_BACKTEST=false`)
- clean git tree (unless `--allow-dirty-git`)
- backend tests
- frontend lint/unit/build

`staging`
- all `dev` checks
- `SECRET_KEY` must be set and not default
- docker compose config check (`docker compose config -q`)
- optional image build (`--docker-build`)

`prod`
- all `staging` checks
- `APP_ENV` must be production-like (`production/prod`)
- KB benchmark threshold gate is enabled by default (`kb_benchmark_mode=required` in `auto` mode)

## KB Benchmark Gate

Gate arguments:
- `--kb-benchmark-mode` = `auto|off|optional|required`
- `--kb-policy` default `backend/config/kb_benchmark_policy.json`
- `--kb-cases` default empty (resolved from policy, then fallback to sample/prod defaults)
- benchmark corpus directory: `backend/config/kb_benchmark_corpus/`
- `--kb-min-precision` default empty (resolved from policy/default)
- `--kb-min-recall` default empty (resolved from policy/default)

`auto` behavior:
- prefer mode from policy profile when present
- fallback mapping without policy: `dev` -> `off`, `staging` -> `optional`, `prod` -> `required`

Current policy baseline (`backend/config/kb_benchmark_policy.json`):
- `dev`: mode `off`, sample cases, thresholds `0.35/0.35`
- `staging`: mode `optional`, `kb_benchmark_cases.kb004.json`, thresholds `0.50/0.75`
- `prod`: mode `required`, `kb_benchmark_cases.kb004.json`, thresholds `0.55/0.80`

Runtime behavior:
- release gate runs benchmark with `--reset-db` for reproducible results per run
- benchmark script seeds isolated corpus from `backend/config/kb_benchmark_corpus/` into `.runtime/kb_benchmark.sqlite3`
- corpus seeding supports file docs (`txt/json/pdf`) and manifest pack (`corpus_pack.json`)

## KB Drift Monitoring (KB-005)

Monitor command:

```bash
python backend/scripts/kb_benchmark_monitor.py --profile prod
python backend/scripts/kb_benchmark_monitor.py --profile staging --mode optional
```

Windows shortcut:

```bat
backend\kb-monitor.cmd --profile prod
```

Outputs:
- benchmark history: `.runtime/kb_benchmark_history/<profile>/benchmark_*.json`
- monitor reports: `.runtime/kb_benchmark_history/<profile>/monitor_*.json`

Drift rules (default):
- compare current metrics against recent history (`drift_lookback=8`)
- require minimum history points (`min_history=3`)
- trigger drift alert when:
  - `precision` drop exceeds `0.08`
  - `recall` drop exceeds `0.05`
- `required` mode alerts are blocking; `optional` mode alerts are non-blocking

CI schedule:
- workflow: `.github/workflows/kb-benchmark-monitor.yml`
- weekly run at `02:00 UTC` every Monday (`cron: 0 2 * * 1`)
- uploads monitor artifacts for trend review

## KB Weekly Review Cadence (KB-006)

Review command:

```bash
python backend/scripts/kb_benchmark_review.py --profile prod --lookback 4
python backend/scripts/kb_benchmark_review.py --profile staging --lookback 4
```

Windows shortcut:

```bat
backend\kb-review.cmd --profile prod --lookback 4
```

Outputs:
- weekly review reports: `.runtime/kb_benchmark_reviews/<profile>/review_*.json`

Weekly cadence workflow:
- `.github/workflows/kb-weekly-review.yml`
- weekly run at `03:00 UTC` every Monday (`cron: 0 3 * * 1`)

Process checklist:
- `docs/Ops/KB_Weekly_Review_Checklist.md`
- threshold decisions recorded in `docs/Ops/KB_Threshold_Changes/`

## KB Monthly Checkpoint (KB-007)

Monthly checkpoint command:

```bash
python backend/scripts/kb_benchmark_monthly_checkpoint.py --profile prod --month 2026-02
python backend/scripts/kb_benchmark_monthly_checkpoint.py --profile staging
```

Windows shortcut:

```bat
backend\kb-monthly-checkpoint.cmd --profile prod --month 2026-02
```

Outputs:
- monthly checkpoint reports: `.runtime/kb_monthly_checkpoints/<profile>/monthly_<YYYY-MM>.json`
- month-end governance records: `docs/Ops/KB_Monthly_Checkpoints/`

Monthly cadence workflow:
- `.github/workflows/kb-monthly-checkpoint.yml`
- monthly run at `04:00 UTC` day `1` (`cron: 0 4 1 * *`)

Template:
- `docs/Ops/KB_Monthly_Checkpoint_Template.md`

## CI Promotion Workflow

Workflow file: `.github/workflows/promotion-gate.yml`

Triggers:
- manual (`workflow_dispatch`) with:
  - `target_env`
  - `run_docker_build`
  - `run_deploy`
  - `rollback_on_failure`
  - `kb_benchmark_mode`
  - `kb_policy`
  - `kb_min_precision`
  - `kb_min_recall`
  - `kb_cases`
- automatic on push to `main` (runs staging gate without docker build)

Artifact:
- `release-gate-report` containing JSON gate report
- `deploy-report` containing deploy/rollback report (when deploy job runs)

## Deploy and Rollback Automation

Deploy script:

```bash
python backend/scripts/deploy_with_rollback.py --env staging --project-name stocktracker-staging
python backend/scripts/deploy_with_rollback.py --env prod --project-name stocktracker-prod --rollback-on-failure
```

Dry-run validation:

```bash
python backend/scripts/deploy_with_rollback.py --env staging --dry-run
```

Windows shortcut:

```bat
backend\deploy-with-rollback.cmd --env staging --rollback-on-failure
```

Behavior:
- backup local SQLite DB before deploy (`.runtime/deploy_backups/...`)
- snapshot current running images into rollback tags
- deploy via `docker compose up -d --build --remove-orphans`
- run backend/frontend health checks and container running checks
- optionally rollback to snapshot images and restore DB backup on failure
- write machine-readable report to `.runtime/deploy_report_*.json`

## Rollback Drill Automation

Drill command:

```bash
python backend/scripts/rollback_drill.py --env staging
python backend/scripts/rollback_drill.py --env prod --retain-count 36
```

Windows shortcut:

```bat
backend\rollback-drill.cmd --env staging
```

Drill behavior:
- uses deploy script with forced initial health failure to exercise rollback path
- default drill mode is `--dry-run` for reproducibility on non-docker runners
- writes archived drill reports to `.runtime/rollback_drills/`
- applies retention policy by count (`--retain-count`)

CI schedule:
- workflow: `.github/workflows/rollback-drill.yml`
- monthly run at `03:00 UTC` on day `1` (`cron: 0 3 1 * *`)
- uploads rollback drill report artifacts

## Promotion Decision Rule

Promote only if:
1. release gate exit code is `0`
2. report `passed=true`
3. no unresolved blocker in report checks

## Threshold Change Governance

Any KB threshold update (`min_precision` / `min_recall` / profile mode) must include:
1. latest monitor trend evidence (`.runtime/kb_benchmark_history/...`)
2. weekly review summary evidence (`.runtime/kb_benchmark_reviews/...`)
3. explicit change request record from `docs/Ops/KB_Threshold_Change_Template.md`
4. acceptance result document under `docs/QA/` (UAT evidence with command/output summary)

Threshold changes are not accepted without reproducible benchmark evidence and sign-off context.

## Remaining Hardening

- Add cloud/environment-specific deployment endpoints (current baseline is docker-compose local/runner).
- Add signed release tag policy.
