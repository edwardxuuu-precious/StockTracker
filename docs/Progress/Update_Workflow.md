# Progress Update Workflow

Last updated: `2026-02-11`

Use this workflow after each development session.

## Required Update Steps

1. Run validation commands.
- `python -m pytest backend/tests -q`
- If release-related changes: `python backend/scripts/release_gate.py --profile dev --skip-docker --allow-dirty-git`

2. Update active QA execution log.
- File: `docs/QA/UAT_Execution_Log_2026-02-11.md`
- Update latest run results and evidence paths.

3. Update actionable backlog.
- File: `docs/Progress/Current_Backlog_2026-02-09.md`
- Ensure each task keeps `ID/Goal/Status/Next Action/Done Criteria`.
- Move completed items to `Completed Tasks (Recent)`.

4. Update project handoff snapshot when major changes land.
- File: `docs/HANDOFF_TO_CODEX_2026-02-10.md`
- Update key code changes, evidence files, quality status, and next actions.

5. Keep runbook/ops in sync when process changes.
- Files: `docs/Runbook.md`, `docs/Ops/Release_Governance.md`
- Add exact commands and required flags for new scripts/workflows.

## Status Vocabulary

- `pending`: not started
- `in_progress`: active work
- `blocked`: waiting for dependency or decision
- `done`: accepted against done criteria

## Cross-Device Resume Rule

When resuming from another device:
1. Read `docs/HANDOFF_TO_CODEX_2026-02-10.md`
2. Read `docs/Progress/Current_Backlog_2026-02-09.md`
3. Read `docs/QA/README.md`
4. Execute the `Next Action` of the highest-priority `in_progress` task
