# StockTracker Current Backlog (2026-02-09)

Last updated: `2026-02-10`

This file is the single source of truth for actionable work items.

## Tracking Schema

Each task must contain:
- `ID`: stable task id
- `Goal`: expected outcome
- `Status`: `pending` | `in_progress` | `blocked` | `done`
- `Next Action`: one concrete next step
- `Done Criteria`: objective acceptance condition

## Active Tasks (Now)

### STRAT-001
- `ID`: STRAT-001
- `Goal`: make the LLM-first strategy generation loop robust for real user prompts (generation -> backtest -> optimization suggestion).
- `Status`: in_progress
- `Next Action`: define and validate 3-5 real prompt templates and compare strategy quality/reproducibility.
- `Done Criteria`: prompts can consistently produce executable strategies and meaningful optimization suggestions with traceable evidence.

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

### CLEAN-001
- `ID`: CLEAN-001
- `Goal`: simplify repository structure without breaking functionality.
- `Status`: done
- `Next Action`: keep archive/report pattern stable for future cleanups.
- `Done Criteria`: runtime artifacts and historical docs moved to `archive/`; active docs reduced to clear entrypoints.

### CLEAN-002
- `ID`: CLEAN-002
- `Goal`: dependency-layer slimming and rebuild verification.
- `Status`: done
- `Next Action`: keep lockfiles and env templates aligned with actual project roots.
- `Done Criteria`: `venv` + `frontend/node_modules` rebuilt, backend/frontend checks pass.

### DOC-001
- `ID`: DOC-001
- `Goal`: align progress/QA/runbook docs with current repository state.
- `Status`: done
- `Next Action`: continue updating this backlog and handoff doc after each major change.
- `Done Criteria`: no broken local markdown links in project docs and all entry documents point to current paths.

### DOC-002
- `ID`: DOC-002
- `Goal`: minimize active QA docs while preserving full historical traceability.
- `Status`: done
- `Next Action`: keep one summary entry per topic and archive milestone-level details by round.
- `Done Criteria`: active QA folder reduced to operational essentials, historical milestone docs moved to `archive/obsolete/`, and references updated.
