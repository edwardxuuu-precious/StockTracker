# StockTracker Current Backlog (2026-02-09)

This file is the single source of truth for actionable work items.

## Tracking Schema

Each task must contain:
- `ID`: stable task id, e.g. `KB-003`
- `Goal`: expected outcome
- `Status`: `pending` | `in_progress` | `blocked` | `done`
- `Next Action`: one concrete next step
- `Done Criteria`: objective acceptance condition

## Active Tasks (Now)

### OPS-003
- `ID`: OPS-003
- `Goal`: connect promotion workflow to real cloud deployment endpoints.
- `Status`: pending
- `Next Action`: define target deployment endpoint shape (API/CLI) and credentials loading policy.
- `Done Criteria`: promotion workflow can deploy to non-local environment without manual docker-compose intervention.

### KB-008
- `ID`: KB-008
- `Goal`: sustain long-horizon KB governance operations and auditability.
- `Status`: pending
- `Next Action`: define quarterly audit checklist for trend quality, threshold decisions, and false-alert rate.
- `Done Criteria`: first quarterly governance audit report is documented and linked to monthly checkpoints.

## Completed Tasks (Recent)

### DATA-001
- `ID`: DATA-001
- `Goal`: local minute/daily data schema and query/ingest APIs.
- `Status`: done
- `Next Action`: monitor production backfill quality.
- `Done Criteria`: local data model and ingestion/query APIs available and stable.

### DATA-002
- `ID`: DATA-002
- `Goal`: provider abstraction with CN/US adapters.
- `Status`: done
- `Next Action`: extend provider reliability monitoring.
- `Done Criteria`: AKShare CN + yfinance US adapters with idempotent ingestion.

### BT-001
- `ID`: BT-001
- `Goal`: replace simulated backtest path with local-data execution.
- `Status`: done
- `Next Action`: continue robustness improvements under BT-002 output.
- `Done Criteria`: backtest runs from local bars only and is reproducible.

### BT-002
- `ID`: BT-002
- `Goal`: calibrate metrics across market regimes and symbols.
- `Status`: done
- `Next Action`: continue collecting broader regime datasets.
- `Done Criteria`: bull/bear/choppy/flat + US/CN regression coverage in test suite.

### KB-001
- `ID`: KB-001
- `Goal`: KB ingest/search/citation baseline.
- `Status`: done
- `Next Action`: improve scale quality via KB-003.
- `Done Criteria`: PDF/TXT/JSON ingestion + hybrid retrieval + citation chain.

### KB-002
- `ID`: KB-002
- `Goal`: governance policy + benchmark + release-threshold integration.
- `Status`: done
- `Next Action`: promote larger corpus thresholds through KB-003.
- `Done Criteria`: policy profiles + benchmark runner + release gate integration working.

### AGENT-001
- `ID`: AGENT-001
- `Goal`: strategy generation/tuning/report workflow.
- `Status`: done
- `Next Action`: improve recommendation quality using richer KB corpus.
- `Done Criteria`: strategy script generation + tuning + report API/UI end-to-end.

### OPS-001
- `ID`: OPS-001
- `Goal`: scheduler reliability baseline.
- `Status`: done
- `Next Action`: tune alert routing policy and failure SLO thresholds.
- `Done Criteria`: scheduler execution, idempotence, and operational visibility meet release standards.

### OPS-002
- `ID`: OPS-002
- `Goal`: release governance and promotion gate baseline.
- `Status`: done
- `Next Action`: extend to OPS-003 cloud endpoint stage.
- `Done Criteria`: release gate + deploy/rollback automation + governance runbook in place.

### OPS-004
- `ID`: OPS-004
- `Goal`: establish scheduled rollback drill with report retention.
- `Status`: done
- `Next Action`: monitor monthly drill artifacts and tune retention policy.
- `Done Criteria`: at least one successful rehearsal report is generated automatically and archived.

### KB-003
- `ID`: KB-003
- `Goal`: expand production benchmark corpus and stabilize threshold pass rate.
- `Status`: done
- `Next Action`: baseline is superseded by KB-004 and KB-005.
- `Done Criteria`: release gate passes `prod` thresholds (`precision>=0.45`, `recall>=0.45`) on representative corpus.

### KB-004
- `ID`: KB-004
- `Goal`: scale benchmark corpus to larger real-world documents and tighten threshold policy.
- `Status`: done
- `Next Action`: continue with KB-005 drift governance.
- `Done Criteria`: benchmark corpus size and threshold policy are documented and enforced in release gate.

### KB-005
- `ID`: KB-005
- `Goal`: add benchmark drift monitoring and periodic threshold recalibration workflow.
- `Status`: done
- `Next Action`: continue with KB-006 multi-week governance cadence.
- `Done Criteria`: benchmark trend history is archived and threshold changes require explicit acceptance evidence.

### KB-006
- `ID`: KB-006
- `Goal`: establish multi-week drift trend review cadence and threshold recalibration decisions.
- `Status`: done
- `Next Action`: continue with KB-007 monthly checkpoint governance.
- `Done Criteria`: at least one evidence-backed threshold review decision is documented using the change template.

### KB-007
- `ID`: KB-007
- `Goal`: operationalize long-run KB trend governance (weekly cadence + monthly threshold review checkpoint).
- `Status`: done
- `Next Action`: continue with KB-008 quarterly governance audit.
- `Done Criteria`: at least one month-end governance checkpoint summarizes weekly reports and any threshold change decisions.

### ENG-001
- `ID`: ENG-001
- `Goal`: clear active framework deprecation warnings.
- `Status`: done
- `Next Action`: guard against regression via regular CI runs.
- `Done Criteria`: backend tests run cleanly without current deprecation warnings.
