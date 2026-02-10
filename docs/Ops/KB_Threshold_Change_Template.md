# KB Threshold Change Template

Use this template when changing KB benchmark policy values.

## 1) Change Info

| Field | Value |
| --- | --- |
| Change ID | `KB-TC-<YYYYMMDD>-<NN>` |
| Date (UTC) | `<YYYY-MM-DD>` |
| Owner | `<name>` |
| Environment Scope | `<staging/prod/both>` |
| Policy File | `backend/config/kb_benchmark_policy.json` |

## 2) Proposed Change

| Item | Current | Proposed | Reason |
| --- | --- | --- | --- |
| Mode | `<off/optional/required>` | `<...>` | `<why>` |
| Min Precision | `<value>` | `<value>` | `<why>` |
| Min Recall | `<value>` | `<value>` | `<why>` |
| Cases File | `<path>` | `<path>` | `<why>` |

## 3) Evidence

- Monitor reports used:
  - `<.runtime/kb_benchmark_history/.../monitor_*.json>`
- Benchmark runs used:
  - `<command + key metrics>`
- Drift analysis summary:
  - `<precision/recall trend and risk assessment>`

## 4) Risk and Rollback

- Expected impact:
  - `<what may fail/pass after this change>`
- Rollback plan:
  - `<how to revert policy quickly>`

## 5) Acceptance

- Linked UAT document:
  - `<docs/QA/UAT_...md>`
- Decision:
  - `<Go/No-Go>`
- Sign-off:
  - `<owner/tester/date>`
