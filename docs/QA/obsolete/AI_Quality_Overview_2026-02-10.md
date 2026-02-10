# StockTracker AI Quality Overview (2026-02-10)

Last updated: `2026-02-10`

## Purpose

This document is the single active summary for AI quality status and evidence entry points.

## Current Baseline

- P0 AI quality tests: implemented and passing in backend test suite.
- Agent benchmark foundation: test sets and runner available under `backend/benchmarks/`.
- Baseline benchmark runs completed with follow-up fix for allocation inference behavior.
- LLM-first readiness has explicit go/no-go checks:
  - `docs/QA/Agent_LLM_Readiness_Checklist_2026-02-10.md`

## What To Run

- Core backend tests: `python -m pytest backend/tests -q`
- AI quality tests: `python -m pytest backend/tests/test_ai_quality.py -q`
- Agent benchmark: `python -m benchmarks.run_agent_benchmark`

## Active QA Documents

- `docs/QA/README.md`
- `docs/QA/UAT_RealUsage_Log_2026-02.md`
- `docs/QA/UAT_TEMPLATE.md`
- `docs/QA/Agent_LLM_Readiness_Checklist_2026-02-10.md`
- `docs/QA/AI_Quality_Overview_2026-02-10.md`

## Historical Detailed Reports (Archived)

Detailed milestone-level QA reports were moved to:
`archive/obsolete/docs_round3_20260210_204843/docs/QA/`

- `AI_Features_Testing_Analysis_2026-02-10.md`
- `P0_AI_Quality_Tests_Summary.md`
- `P1_AI_Benchmark_Infrastructure_Summary.md`
- `P2_Benchmark_Baseline_Summary.md`
- `Agent_Allocation_Fix_Summary.md`

Use archived files when you need historical implementation detail or original execution notes.
