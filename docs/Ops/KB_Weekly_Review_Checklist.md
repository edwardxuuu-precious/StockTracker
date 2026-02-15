# KB Weekly Review Checklist

Last updated: `2026-02-11`

## Weekly Checklist

1. Confirm `backend/config/kb_benchmark_policy.json` is unchanged or documented.
2. Run KB benchmark monitor:
   - `python backend/scripts/kb_benchmark_monitor.py`
3. Review precision/recall trend against policy thresholds.
4. Confirm no unresolved KB-related P0/P1 defects in active QA docs.
5. Record outcomes in project progress log and link evidence path.

## Escalation Triggers

- Precision below policy threshold for two consecutive runs.
- Recall below policy threshold in production profile.
- Retrieval fallback ratio unexpectedly spikes in telemetry.
