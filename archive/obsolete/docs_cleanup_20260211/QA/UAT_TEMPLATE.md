# UAT Template

## 1) Basic Info

| Field | Value |
| --- | --- |
| Project | `StockTracker` |
| Release Version | `<vX.Y.Z>` |
| Git Branch | `<branch>` |
| Commit / Tag | `<commit-or-tag>` |
| Environment | `<Local / Staging / Prod-like>` |
| Backend URL | `<http://localhost:<backend_port>>` |
| Frontend URL | `<http://localhost:5173>` |
| Tester | `<name>` |
| Test Date | `<YYYY-MM-DD>` |

## 2) Scope

### In Scope
- `<BL-xxx / feature-1>`
- `<BL-xxx / feature-2>`

### Out of Scope
- `<not covered item>`
- `<dependency not ready>`

## 3) Entry Criteria (must pass before UAT)

- [ ] Backend and frontend can both start successfully.
- [ ] Backend port is confirmed from `.runtime/backend-port.txt`.
- [ ] API documentation page is reachable on `http://localhost:<backend_port>/docs`.
- [ ] Test data is prepared and isolated with a unique prefix.
- [ ] Critical dependencies are available (DB/network/API keys if needed).
- [ ] Required test accounts/permissions are ready.

## 4) Test Data Plan

| Data ID | Purpose | Input | Expected Baseline |
| --- | --- | --- | --- |
| `<DATA-01>` | `<what to verify>` | `<payload / setup>` | `<baseline>` |

## 5) UAT Test Cases

Use one row per test case.

| Case ID | BL | Scenario | Steps | Expected Result | Actual Result | Status (`PASS`/`FAIL`/`BLOCKED`) | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `<UAT-001>` | `<BL-xxx>` | `<short title>` | `<step-by-step>` | `<expected>` | `<actual>` | `<status>` | `<screenshot/log>` | `<BUG-xxx>` |

## 6) Defect Log

| Defect ID | Severity (`P0/P1/P2`) | Summary | Repro Steps | Impact | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `<BUG-001>` | `<P1>` | `<summary>` | `<steps>` | `<impact>` | `<name>` | `<Open/Fixed/Verified>` |

## 7) Exit Criteria

- [ ] All in-scope test cases executed.
- [ ] `P0 = 0`.
- [ ] `P1` accepted threshold is met (fill threshold below).
- [ ] Regression smoke path is passed.
- [ ] Required evidence is attached.

Acceptance threshold for `P1`:
- `<example: P1 <= 1 and has workaround>`

## 8) Final Decision

| Decision | Value |
| --- | --- |
| Go / No-Go | `<Go or No-Go>` |
| Residual Risk | `<short description>` |
| Follow-up Actions | `<action list>` |

Sign-off:

| Role | Name | Date | Sign |
| --- | --- | --- | --- |
| QA/UAT | `<name>` | `<YYYY-MM-DD>` | `<sign>` |
| Dev | `<name>` | `<YYYY-MM-DD>` | `<sign>` |
| PM/Owner | `<name>` | `<YYYY-MM-DD>` | `<sign>` |
