# KB Weekly Review Checklist

Use this checklist once per week for `KB-006` trend governance.

## 1) Collect Inputs

- [ ] Latest monitor reports exist:
  - `.runtime/kb_benchmark_history/prod/monitor_*.json`
  - `.runtime/kb_benchmark_history/staging/monitor_*.json`
- [ ] Latest benchmark reports exist:
  - `.runtime/kb_benchmark_history/prod/benchmark_*.json`
  - `.runtime/kb_benchmark_history/staging/benchmark_*.json`
- [ ] Weekly review JSON generated:
  - `.runtime/kb_benchmark_reviews/<profile>/review_*.json`

## 2) Validate Trend Health

- [ ] No unexpected blocking alerts in latest 4 points.
- [ ] Precision trend is stable or improving.
- [ ] Recall trend is stable or improving.
- [ ] Failed monitor points count is `0` in review window.

## 3) Decision Rule

- [ ] If blocking alerts exist: choose `investigate_before_change`.
- [ ] If 4+ points all healthy and margin >= `+0.10`: choose `consider_tighten`.
- [ ] Otherwise: choose `keep_thresholds`.

## 4) Record Decision

- [ ] Create/update threshold change record using:
  - `docs/Ops/KB_Threshold_Change_Template.md`
- [ ] Link evidence files (monitor/review JSON paths).
- [ ] Link acceptance evidence under `docs/QA/`.

## 5) Update Project State

- [ ] Update `docs/Progress/Current_Backlog_2026-02-09.md`.
- [ ] Update `docs/Progress/Master_Progress.md`.
- [ ] If thresholds changed, update:
  - `backend/config/kb_benchmark_policy.json`
  - `docs/Ops/Release_Governance.md`
