# KB Monthly Checkpoint Template

Use this template for month-end KB governance review.

## 1) Basic Info

| Field | Value |
| --- | --- |
| Month | `<YYYY-MM>` |
| Profile | `<prod/staging>` |
| Owner | `<name>` |
| Generated At (UTC) | `<timestamp>` |
| Runtime Report | `<.runtime/kb_monthly_checkpoints/.../monthly_<YYYY-MM>.json>` |

## 2) Metrics Summary

| Metric | Value |
| --- | --- |
| Monitor Points | `<n>` |
| Review Points | `<n>` |
| Threshold Change Records | `<n>` |
| Avg Precision | `<value>` |
| Avg Recall | `<value>` |
| Failed Monitor Points | `<n>` |
| Total Alerts | `<n>` |
| Governance Status | `<stable/attention_required/candidate_for_threshold_change/insufficient_data>` |

## 3) Decision Review

- Latest review decision:
  - `<keep_thresholds/consider_tighten/investigate_before_change/...>`
- Review decision counts:
  - `<key:value>`
- Threshold changes this month:
  - `<KB-TC ids or none>`

## 4) Actions

- [ ] Keep thresholds unchanged.
- [ ] Propose threshold change (if evidence supports).
- [ ] Investigate regression root cause (if attention required).

Selected action:
- `<final decision>`

## 5) Evidence Links

- Monitor reports:
  - `<paths>`
- Weekly review reports:
  - `<paths>`
- Threshold change records:
  - `<paths>`
- UAT records:
  - `<docs/QA/UAT_...>`
