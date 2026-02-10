# StockTracker Current Backlog (2026-02-08)

This backlog is aligned with current code state and latest UAT results.

## P0 (Now)

### BUG-003 Quote refresh resilience

- Goal: remove noisy failure experience when provider returns empty history.
- Scope:
  - keep latest known price when refresh fails
  - show clear user message with actionable guidance
  - avoid breaking holdings table rendering
- Done criteria:
  - no crash
  - error message is clear and mapped to UI labels
  - regression scenario documented in UAT

### Progress doc consistency

- Goal: make progress docs match actual delivered scope.
- Scope:
  - update master progress
  - add current backlog snapshot
  - mark stale references clearly
- Done criteria:
  - a new contributor can read current status without code archaeology

## P1 (Next)

### Strategy/backtest UX refinement

- Separate "create strategy" and "run backtest" responsibilities more clearly.
- Add explicit active-result indicator (already started) and refine row/state consistency.
- Consider adding editable strategy list panel for existing strategies.

### Error UX standardization

- Consolidate form and request errors into a consistent pattern.
- Ensure stale result blocks are explicitly marked as previous runs after failed submission.

## P2 (Later)

### Security and deployment baseline

- Add minimal CI pipeline:
  - backend tests
  - frontend unit + lint + build
  - `pip-audit` and `npm audit`
- Add deployment baseline files (`Dockerfile`, `docker-compose`, env templates).
- Introduce auth plan for non-local environments.
