# Release Governance

Last updated: `2026-02-11`

## Purpose

Define a consistent release gate process for `dev`, `staging`, and `prod`.

## Required Checks Before Promotion

1. Backend tests: `venv\Scripts\python -m pytest backend\tests -q`
2. Frontend quality: `cd frontend && npm run lint && npm run test:unit && npm run build`
3. Docs link integrity: `powershell -NoProfile -ExecutionPolicy Bypass -File scripts/check-doc-links.ps1`
4. Release gate script:
   - Dev: `python backend/scripts/release_gate.py --profile dev`
   - Staging: `python backend/scripts/release_gate.py --profile staging --skip-docker`
   - Prod: `python backend/scripts/release_gate.py --profile prod --docker-build`

## GitHub Workflow References

- CI: `.github/workflows/ci.yml`
- Promotion gate: `.github/workflows/promotion-gate.yml`

## Evidence

- Store cleanup/release evidence under `reports/cleanup/` or `.runtime/` artifacts attached by workflows.
