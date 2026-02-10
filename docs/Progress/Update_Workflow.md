# Progress Update Workflow

Last updated: `2026-02-09`

Use this workflow after each development session.

## Required Update Steps

1. Run validation commands.
- `python -m pytest backend/tests -q`
- if release-related changes: `python backend/scripts/release_gate.py --profile dev --skip-docker --allow-dirty-git`

2. Update acceptance snapshot.
- File: `docs/QA/Acceptance_Checklist_2026-02-09.md`
- Update latest pass/fail numbers and any new acceptance checks.

3. Update actionable backlog.
- File: `docs/Progress/Current_Backlog_2026-02-09.md`
- Ensure each task keeps `ID/Goal/Status/Next Action/Done Criteria`.
- Move completed items to `Completed Tasks (Recent)`.

4. Update global status and risks.
- File: `docs/Progress/Master_Progress.md`
- Update `Current Risks`, `Next Focus`, and `Latest Implementation Notes`.

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
1. Read `docs/Progress/Master_Progress.md`
2. Read `docs/Progress/Current_Backlog_2026-02-09.md`
3. Execute the `Next Action` of the highest-priority `in_progress` task
