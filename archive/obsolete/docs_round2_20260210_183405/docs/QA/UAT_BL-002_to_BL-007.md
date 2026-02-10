# UAT Checklist: BL-002 to BL-007

## 1) Basic Info

| Field | Value |
| --- | --- |
| Project | `StockTracker` |
| Scope | `BL-002 ~ BL-007` |
| Environment | `Local (Windows)` |
| Backend URL | `http://localhost:8002` |
| Frontend URL | `http://localhost:5173` |
| Tester | `edwar` |
| Test Date | `2026-02-07` |

---

## 2) Global Pre-check

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `PRE-01` | Run `start-all.bat` | Backend/frontend both keep running | `PASS` | Backend + frontend windows started |
| `PRE-02` | Read backend port from `.runtime/backend-port.txt` (e.g. `8002`) | Port file exists and has a valid port | `PASS` | Port file value `8002` |
| `PRE-03` | Open `http://localhost:<backend_port>/docs` | Swagger works | `PASS` | `http://localhost:8002/docs` reachable |
| `PRE-04` | Open frontend URL | Home page renders correctly | `PASS` | Portfolio list page rendered |
| `PRE-05` | Create a unique test prefix (e.g. `UAT_20260207_`) | Test data is isolated | `PASS` | Prefix used: `UAT_0207_` |

---

## 3) BL-002: Holding API de-dup and regression

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL2-01` | Check holdings endpoints in `/docs` | No duplicate same-method same-path endpoints | `PASS` | Swagger check done, no duplicate same path+method |
| `BL2-02` | `POST /api/v1/portfolios/` with `initial_capital=1000` | 201, `cash_balance=1000`, return portfolio id | `PASS` | `portfolio_id=6`, `cash_balance=1000` |
| `BL2-03` | `POST /portfolios/{id}/holdings` with `AAPL qty=2 avg_cost=100` | 201, holding created, cash becomes `800` | `PASS` | `holding_id=6`, portfolio cash `800` |
| `BL2-04` | `PUT /portfolios/{id}/holdings/{holding_id}` to `qty=3 avg_cost=90` | 200, market value `270`, cash becomes `730` | `PASS` | Response `market_value=270`, portfolio cash `730` |
| `BL2-05` | `DELETE /portfolios/{id}/holdings/{holding_id}` | 204, holding removed, cash returns to `1000` | `PASS` | Delete 204, GET portfolio cash `1000` |
| `BL2-06` | Add an expensive holding exceeding cash | 400 with clear `Insufficient cash balance` | `PASS` | 400 `Insufficient cash balance. Available: $1000.00` |
| `BL2-07` | Update/delete non-existent holding id | 404 with clear error | `PASS` | PUT/DELETE `holding_id=999999` -> 404 `Holding not found` |

---

## 4) BL-003: Minimum automated test baseline

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL3-01` | Run `venv\Scripts\python.exe -m pytest backend\tests -q` | All backend tests pass | `PASS` | `14 passed, 10 warnings` |
| `BL3-02` | Run `cd frontend && npm run test:unit` | Unit tests pass | `PASS` | `9 passed, 0 failed` |
| `BL3-03` | Run `cd frontend && npm run lint` | No lint errors | `PASS` | ESLint completed with no errors |
| `BL3-04` | Run `cd frontend && npm run build` | Build completes successfully | `PASS` | Vite build success; preflight passed |
| `BL3-05` | Smoke flow: list portfolio -> detail -> one write action | No functional regression | `PASS` | Re-tested on `UAT_0208_FIX_REG`: same symbol merged into one row; empty-holdings state keeps `current_value == cash_balance` |

---

## 5) BL-004: Trade semantics and PnL correctness

Recommended fixed scenario:
- Initial capital `1000`
- Buy `AAPL 2 @100 commission=1`
- Buy `AAPL 1 @120 commission=0`
- Sell `AAPL 1 @130 commission=1`

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL4-01` | Execute first buy | Cash `1000 -> 799`, position qty `2` | `PASS` | `portfolio_id=7` cash `799`, qty `2`, avg `100.5` |
| `BL4-02` | Execute second buy | Cash `799 -> 679`, avg cost `107` | `PASS` | cash `679`, qty `3`, avg `107`, MV `360` |
| `BL4-03` | Execute sell | Cash `679 -> 808`, remaining qty `2`, avg cost stays `107` | `PASS` | cash `808`, qty `2`, avg `107` |
| `BL4-04` | Check SELL realized PnL in trades table | Realized PnL = `22` | `PASS` | Trades response: `realized_pnl=22` |
| `BL4-05` | Sell quantity greater than holding | 400 with quantity-insufficient error | `PASS` | 400 `Insufficient holding quantity` |
| `BL4-06` | SELL symbol not in holdings | 400 with no-holding error | `PASS` | 400 `No holdings found for symbol MSFT` |
| `BL4-07` | SELL with invalid commission (too large) | 400 with validation message | `PASS` | 400 `Commission cannot exceed trade proceeds` |
| `BL4-08` | Frontend trade form invalid input | Client-side validation blocks submit | `PASS` | Field errors shown and submit blocked |

---

## 6) BL-005: Realtime quotes + cache observability

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL5-01` | `GET /api/v1/quotes/AAPL` first call | `cache_hit=false`, quote payload complete | `BLOCKED` | 502 `yfinance: yfinance returned empty history` |
| `BL5-02` | Call same quote again | `cache_hit=true` | `BLOCKED` | Depends on BL5-01 success; no successful quote response available |
| `BL5-03` | `GET /api/v1/quotes/AAPL?refresh=true` | Force refresh, `cache_hit=false` | `BLOCKED` | Upstream quote unavailable (502) |
| `BL5-04` | `GET /api/v1/quotes/batch?symbols=AAPL,MSFT,GOOGL` | Returns 3 symbols with prices | `BLOCKED` | Upstream quote unavailable (502) |
| `BL5-05` | `GET /api/v1/quotes/stats` | `hits/misses/hit_rate/cache_size/ttl` visible | `PASS` | Stats fields visible; sample: `cache_hits=0, cache_misses=6, ttl_seconds=60` |
| `BL5-06` | Portfolio detail page click refresh quote | Refresh time updates; values re-calc in UI | `BLOCKED` | No successful quote source, cannot verify success-path recalc |
| `BL5-07` | Trigger quote failure case (bad symbol/network issue) | Clear error feedback; page not broken | `PASS` | UI red error text displayed; page remained usable |

---

## 7) BL-006: Analytics dashboard + CSV export

Recommended verification dataset:
- Initial capital `100000`
- Buy `AAPL 100 @150`
- Buy `MSFT 50 @300`
- Sell `AAPL 50 @160`

Expected calculation:
- Cash `78000`
- Holdings MV `23000`
- Current value `101000`
- Total return `1000` (`1.00%`)
- Realized `500`, Unrealized `500`

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL6-01` | Open `/analytics` and select portfolio | Data loads without UI errors | `PASS` | Analytics page loaded with portfolio `UAT_0207_BL6_Portfolio` |
| `BL6-02` | Verify summary cards | Values match expected calculation | `PASS` | Total assets `101000`, total return `+1000`, realized `500`, unrealized `500` |
| `BL6-03` | Verify allocation chart | Weights align with market value proportions | `PASS` | MSFT `65.22%`, AAPL `34.78%` (matches `15000:8000`) |
| `BL6-04` | Verify trend chart | Trend endpoint data is rendered | `PASS` | Trend chart rendered with final jump at `AAPL SELL` |
| `BL6-05` | Verify monthly realized PnL chart | Month entries and trade counts are correct | `PASS` | `2026-02` monthly realized PnL `+500` displayed |
| `BL6-06` | Export `summary` CSV | File downloaded, headers/data complete | `PASS` | Summary CSV headers/data correct (`current_value=101000`, `total_return=1000`) |
| `BL6-07` | Export `holdings` CSV | File downloaded, holdings rows correct | `PASS` | Holdings CSV contains MSFT/AAPL rows with expected values |
| `BL6-08` | Export `trades` CSV | File downloaded, trades rows correct | `PASS` | Trades CSV contains 3 rows with BUY/BUY/SELL and expected realized PnL |
| `BL6-09` | Select a no-trade/no-holding portfolio | Empty-state shown cleanly | `PASS` | Analytics empty-state rendered cleanly for `testtest` portfolio |

---

## 8) BL-007: Strategy backtest skeleton

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL7-01` | Open `/strategies` page | Strategy/backtest page renders correctly | `PASS` | Strategy/backtest page rendered normally with create/run sections |
| `BL7-02` | Create `moving_average` strategy | 201, strategy appears in list/select | `PASS` | `UAT_0208_BL7_MA` created and visible in run selector |
| `BL7-03` | Create `rsi` strategy | 201, RSI params persisted | `PASS` | `UAT_0208_BL7_RSI` created; selector shows strategy; RSI params displayed as `14/30/70` |
| `BL7-04` | Create `momentum` strategy | 201, momentum params persisted | `PASS` | `UAT_0208_BL7_MOM` created and visible in run selector |
| `BL7-05` | Run backtest with valid inputs | Backtest status `completed`, id generated | `PASS` | Run success banner shows `回测完成 (ID: 1)` |
| `BL7-06` | View backtest list | New record visible with `return` and `trade_count` | `PASS` | List shows `#1`, status `completed`, return `+7.03%`, trades `44` |
| `BL7-07` | Open backtest detail | Metrics present (`final_value`, `sharpe`, `drawdown`, `win_rate`) | `PASS` | Detail cards visible: final value `107,034.59`, sharpe `1.7503`, drawdown `-1.38%`, win rate `100%` |
| `BL7-08` | Compare detail trades count vs summary trade_count | Counts are consistent | `PASS` | Summary `交易次数:44` matches list `44` and detail trade records |
| `BL7-09` | Check equity curve chart rendering | Curve appears with no runtime errors | `PASS` | Equity curve rendered normally with no page errors |
| `BL7-10` | Invalid date range (`start > end`) run | 400 validation error | `PASS` | UI shows clear CN error + guidance; detail panel cleared; history hint shown |
| `BL7-11` | Run with non-existent strategy_id | 404 `Strategy not found` | `PASS` | Swagger returns 404 with detail `Strategy not found` |
| `BL7-12` | Reload page and reopen same backtest | Persisted result remains queryable | `PASS` | Refresh + reopen `#1` consistent with no errors; selected-task highlight and context banner remain correct |

---

## 9) Cross-BL Release Gate

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `GATE-01` | End-to-end smoke: create portfolio -> trade -> refresh quote -> analytics -> run backtest | Full critical path works without blocker | `PASS` | `UAT_0208_GATE1` flow completed end-to-end; quote refresh re-tested after fallback fix, price updates normally with no error |
| `GATE-02` | Re-run all automated checks | Backend tests + frontend lint/test/build all pass | `PASS` | Backend pytest pass; frontend test/lint/build pass |
| `GATE-03` | Review unresolved defects | `P0=0`, `P1` within accepted threshold | `PASS` | `P0=0`; all `P1` defects (`BUG-001`, `BUG-002`) closed; `BUG-003` closed; `BUG-004/BUG-005/BUG-006` focused retest passed and closed; post-gate `BUG-007` retest passed and closed |

---

## 10) Defect Log

| Defect ID | Severity (`P0/P1/P2`) | Case ID | Summary | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| `BUG-001` | `P1` | `BL3-05` | Same symbol (`AAPL`) appears as multiple holding rows in one portfolio detail page; holdings count treated as multiple stocks | `Closed (Verified)` | `Dev` |
| `BUG-002` | `P1` | `BL3-05` | Portfolio aggregate inconsistency: observed `holdings=[]` while `current_value` remained above `cash_balance` (`1270` vs `1000`) | `Closed (Verified)` | `Dev` |
| `BUG-003` | `P2` | `BL5-01/02/03/04/06` | Real-time quote success-path blocked in current environment: quote APIs return 502 (`yfinance returned empty history`) | `Closed (Verified)` | `Dev + Env` |
| `BUG-004` | `P2` | `BL6-09` | Empty portfolio detail page shows `最后更新` as `1970/1/1 08:00:00` when no update exists (`updated_at=null` fallback issue) | `Closed (Verified)` | `Dev` |
| `BUG-005` | `P2` | `BL7-03` | Strategy page IA/UX confusion: create-form region also acts as selected-strategy detail source; users expect parameters to be viewed/edited in run-backtest context | `Closed (Verified)` | `Dev + UX` |
| `BUG-006` | `P2` | `BL7-03/BL7-04` | Missing strategy management UX: no dedicated strategy list/detail/edit/save flow for existing strategies in frontend | `Closed (Verified)` | `Dev + UX` |
| `BUG-007` | `P2` | `Post-Gate / Trade validation` | BUY trade accepted invalid symbols (e.g. `INVALID123`) and response time was too long; expected quick rejection for invalid symbols | `Closed (Verified)` | `Dev` |

### 10.1) Issue Process Log (Detailed, No Root Cause Yet)

| Seq | Time (Local) | Operation | Expected | Actual | Linked Defect / Outcome |
| --- | --- | --- | --- | --- | --- |
| `L-01` | `2026-02-07` | Run BL2 flow on `portfolio_id=6` (create, add holding, update, delete, error paths) | Data stays consistent across API and UI | BL2 API checks passed, but later smoke on same dataset exposed inconsistencies | Context for `BUG-001`, `BUG-002` |
| `L-02` | `2026-02-07` | BL3 smoke in portfolio detail after mixed operations | One symbol should appear as one consolidated holding row | Same symbol (`AAPL`) shown in multiple rows, holdings count shown as `2` for one stock code | `BUG-001` confirmed |
| `L-03` | `2026-02-07` | Swagger `GET /api/v1/portfolios/6` after holding cleanup | `holdings=[]` and `current_value` aligned with `cash_balance` | Observed `holdings=[]`, `cash_balance=1000`, but `current_value=1270` | `BUG-002` confirmed |
| `L-04` | `2026-02-07` | Execute BL4 on clean portfolio (`portfolio_id=7`) | Trade semantics and PnL calculations should pass | `BL4-01` to `BL4-08` all passed | BL4 marked `PASS` |
| `L-05` | `2026-02-07` | Start BL5 with `GET /api/v1/quotes/AAPL` | 200 with quote payload and `cache_hit=false` | 502 `yfinance: yfinance returned empty history` | `BUG-003`, BL5 success path blocked |
| `L-06` | `2026-02-07` | Retry multiple symbols + frontend refresh quote | At least one symbol quote should succeed | AAPL/MSFT/TSLA/600519 all failed in this environment; frontend showed clear red error and remained stable | `BL5-07 PASS`; BL5 success-path cases blocked |
| `L-07` | `2026-02-08` | Build BL6 dataset (`portfolio_id=8`) and compare API vs analytics values | Aggregates should be consistent across endpoints/pages | `GET /portfolios/8` showed `current_value=108000`, while analytics summary showed `101000` and matched expected formula | `BUG-002` reconfirmed in new dataset |
| `L-08` | `2026-02-08` | Validate BL6 exports and empty-portfolio views | Exports and empty states should be clear and consistent | BL6 CSV exports passed; empty analytics state passed; empty portfolio detail page showed `最后更新` as Unix epoch display | `BL6-08 PASS`, `BL6-09 PASS`, `BUG-004` |
| `L-09` | `2026-02-08` | BL7 RSI parameter persistence confirmation discussion | Persisted strategy params should be checked in intuitive context | Tester reported current IA causes misunderstanding (create area vs run area ownership) | `BUG-005` logged |
| `L-10` | `2026-02-08` | BL7 momentum creation and strategy UX review | Existing strategies should be browsable/editable from dedicated management area | Momentum strategy creation succeeded; tester reported missing strategy list/edit/save UX for existing strategies | `BL7-04 PASS`, `BUG-006` |
| `L-11` | `2026-02-08` | Run first valid backtest and inspect result view | Backtest should complete and expose list + metrics + curve + trades | Backtest `ID:1` completed; list/detail/curve/trades all rendered and numerically consistent (`trade_count=44`) | `BL7-05~BL7-09 PASS` |
| `L-12` | `2026-02-08` | Reload strategies page and reopen task `#1` | Persisted task should remain queryable with consistent metrics | Reload + reopen succeeded; final value and trade count stayed consistent, no errors | `BL7-12 PASS` |
| `L-13` | `2026-02-08` | Execute `GATE-01` smoke with `UAT_0208_GATE1` | End-to-end chain should be operable from portfolio to analytics and strategy backtest | Portfolio creation/trade/analytics export/backtest all succeeded; quote refresh entered known degraded path with clear error feedback and no page break | `GATE-01 PASS (Degraded)` |
| `L-14` | `2026-02-08` | Execute `GATE-03` defect triage | `P0=0` and `P1` within release threshold | `P0=0` confirmed, but `P1` defects remain open (`BUG-001`, `BUG-002`); quote dependency issue (`BUG-003`) still blocks success-path acceptance | `GATE-03 FAIL (No-Go)` |
| `L-15` | `2026-02-08` | Implement fix for duplicate holdings and stale current value | Same symbol should not fan out into multiple rows; portfolio value should stay consistent with cash + holdings | Added in-session flush before portfolio aggregate recompute, merged duplicate symbol holdings in legacy/add/update/trade paths, and added regression tests; backend suite passed (`14 passed`) | `BUG-001/BUG-002 -> Ready for Retest` |
| `L-16` | `2026-02-08` | Manual retest for `BUG-001` and `BUG-002` on `UAT_0208_FIX_REG` | Same-symbol buys should stay one row; after full sell, `holdings=[]` and `current_value==cash_balance` | Frontend and Swagger both confirmed: one `AAPL` row with qty `3`, then sell-all to empty holdings with `cash_balance=1040` and `current_value=1040` | `BUG-001/BUG-002 Closed (Verified); GATE-03 PASS (Conditional)` |
| `L-17` | `2026-02-08` | Implement quote fallback for `BUG-003` (`yfinance -> stooq`) | When Yahoo is rate-limited/empty-history, quote endpoint should still return usable data | Added `StooqQuoteProvider` and provider-chain fallback; local verification for `/api/v1/quotes/AAPL?refresh=true` returned `200`, `source=stooq`, `price=278.12` under Yahoo `429` | `BUG-003 -> Ready for Retest` |
| `L-18` | `2026-02-08` | Manual retest for `BUG-003` (Swagger + frontend quote refresh) | Single quote should return `200` with price, cache should hit on second call, frontend refresh should not show previous error | Verified: `/api/v1/quotes/AAPL?refresh=true` returned `200` and correct price, subsequent `/api/v1/quotes/AAPL` returned `cache_hit=true`, portfolio detail refresh displayed updated quote (`source=stooq`) with no red error | `BUG-003 Closed (Verified); GATE-01 PASS` |
| `L-19` | `2026-02-08` | Implement UX fixes for `BUG-004/BUG-005/BUG-006` | Empty-date display should avoid epoch fallback; strategy management should be explicit and editable from dedicated area; selected backtest should be clearly indicated | Added `formatDateTime` fallback (`--`) for null/invalid timestamps in portfolio detail; added dedicated strategy management panel (list/select/edit/save/apply-to-run); strengthened selected-task highlight and current-result banner in backtest list/detail | `BUG-004/BUG-005/BUG-006 -> Ready for Retest` |
| `L-20` | `2026-02-08` | Focused retest for `BUG-004/BUG-005/BUG-006` | Empty portfolio should show `最后更新=--`; strategy management edit/save should persist; run panel parameters should match selected strategy context | Tester confirmed all checks passed: empty portfolio timestamp display correct, strategy management save+reload persisted, and run-panel context/selected-task highlight consistent | `BUG-004/BUG-005/BUG-006 Closed (Verified); GATE-03 PASS` |
| `L-21` | `2026-02-08` | Post-gate manual validation found invalid symbol buy and latency issue | BUY invalid symbol should be rejected quickly and must not create holdings/trades | Initial check failed: BUY `INVALID123` succeeded and created holding/trade; UI wait was noticeably long | `BUG-007 logged` |
| `L-22` | `2026-02-08` | Implement and retest `BUG-007` (trade-time symbol validation + faster verification path) | BUY invalid symbol should return `400` quickly; SELL existing holdings should remain available | Verified: BUY `INVALID123` returned `400` with clear message, latency reduced, and no new trade created; SELL on existing valid holding remained successful | `BUG-007 Closed (Verified)` |

---

## 11) Final Sign-off

- Go / No-Go: `Go`
- Residual risk: `No open P0/P1 defects in BL-002 ~ BL-007 scope; remaining risk is routine future UX iteration, not release blocking`
- Follow-up actions: `Proceed with next bug batch and keep regression checklist updated per change set`

| Role | Name | Date | Sign |
| --- | --- | --- | --- |
| QA/UAT | `edwar` | `2026-02-08` | `< >` |
| Dev | `<fill>` | `<YYYY-MM-DD>` | `< >` |
| PM/Owner | `<fill>` | `<YYYY-MM-DD>` | `< >` |

