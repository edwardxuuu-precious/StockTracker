# UAT Checklist: BL-002 to BL-007

## 1) Basic Info

| Field | Value |
| --- | --- |
| Project | `StockTracker` |
| Scope | `BL-002 ~ BL-007` |
| Environment | `Local` |
| Backend URL | `http://localhost:<backend_port>` |
| Frontend URL | `http://localhost:5173` |
| Tester | `<fill>` |
| Test Date | `<YYYY-MM-DD>` |

---

## 2) Global Pre-check

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `PRE-01` | Run `start-all.bat` | Backend/frontend both keep running | `< >` | `< >` |
| `PRE-02` | Read backend port from `.runtime/backend-port.txt` (e.g. `8002`) | Port file exists and has a valid port | `< >` | `< >` |
| `PRE-03` | Open `http://localhost:<backend_port>/docs` | Swagger works | `< >` | `< >` |
| `PRE-04` | Open frontend URL | Home page renders correctly | `< >` | `< >` |
| `PRE-05` | Create a unique test prefix (e.g. `UAT_20260207_`) | Test data is isolated | `< >` | `< >` |

---

## 3) BL-002: Holding API de-dup and regression

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL2-01` | Check holdings endpoints in `/docs` | No duplicate same-method same-path endpoints | `< >` | `< >` |
| `BL2-02` | `POST /api/v1/portfolios/` with `initial_capital=1000` | 201, `cash_balance=1000`, return portfolio id | `< >` | `< >` |
| `BL2-03` | `POST /portfolios/{id}/holdings` with `AAPL qty=2 avg_cost=100` | 201, holding created, cash becomes `800` | `< >` | `< >` |
| `BL2-04` | `PUT /portfolios/{id}/holdings/{holding_id}` to `qty=3 avg_cost=90` | 200, market value `270`, cash becomes `730` | `< >` | `< >` |
| `BL2-05` | `DELETE /portfolios/{id}/holdings/{holding_id}` | 204, holding removed, cash returns to `1000` | `< >` | `< >` |
| `BL2-06` | Add an expensive holding exceeding cash | 400 with clear `Insufficient cash balance` | `< >` | `< >` |
| `BL2-07` | Update/delete non-existent holding id | 404 with clear error | `< >` | `< >` |

---

## 4) BL-003: Minimum automated test baseline

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL3-01` | Run `venv\Scripts\python.exe -m pytest backend\tests -q` | All backend tests pass | `< >` | `< >` |
| `BL3-02` | Run `cd frontend && npm run test:unit` | Unit tests pass | `< >` | `< >` |
| `BL3-03` | Run `cd frontend && npm run lint` | No lint errors | `< >` | `< >` |
| `BL3-04` | Run `cd frontend && npm run build` | Build completes successfully | `< >` | `< >` |
| `BL3-05` | Smoke flow: list portfolio -> detail -> one write action | No functional regression | `< >` | `< >` |

---

## 5) BL-004: Trade semantics and PnL correctness

Recommended fixed scenario:
- Initial capital `1000`
- Buy `AAPL 2 @100 commission=1`
- Buy `AAPL 1 @120 commission=0`
- Sell `AAPL 1 @130 commission=1`

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL4-01` | Execute first buy | Cash `1000 -> 799`, position qty `2` | `< >` | `< >` |
| `BL4-02` | Execute second buy | Cash `799 -> 679`, avg cost `107` | `< >` | `< >` |
| `BL4-03` | Execute sell | Cash `679 -> 808`, remaining qty `2`, avg cost stays `107` | `< >` | `< >` |
| `BL4-04` | Check SELL realized PnL in trades table | Realized PnL = `22` | `< >` | `< >` |
| `BL4-05` | Sell quantity greater than holding | 400 with quantity-insufficient error | `< >` | `< >` |
| `BL4-06` | SELL symbol not in holdings | 400 with no-holding error | `< >` | `< >` |
| `BL4-07` | SELL with invalid commission (too large) | 400 with validation message | `< >` | `< >` |
| `BL4-08` | Frontend trade form invalid input | Client-side validation blocks submit | `< >` | `< >` |

---

## 6) BL-005: Realtime quotes + cache observability

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL5-01` | `GET /api/v1/quotes/AAPL` first call | `cache_hit=false`, quote payload complete | `< >` | `< >` |
| `BL5-02` | Call same quote again | `cache_hit=true` | `< >` | `< >` |
| `BL5-03` | `GET /api/v1/quotes/AAPL?refresh=true` | Force refresh, `cache_hit=false` | `< >` | `< >` |
| `BL5-04` | `GET /api/v1/quotes/batch?symbols=AAPL,MSFT,GOOGL` | Returns 3 symbols with prices | `< >` | `< >` |
| `BL5-05` | `GET /api/v1/quotes/stats` | `hits/misses/hit_rate/cache_size/ttl` visible | `< >` | `< >` |
| `BL5-06` | Portfolio detail page click "刷新报价" | Refresh time updates; values re-calc in UI | `< >` | `< >` |
| `BL5-07` | Trigger quote failure case (bad symbol/network issue) | Clear error feedback; page not broken | `< >` | `< >` |

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
| `BL6-01` | Open `/analytics` and select portfolio | Data loads without UI errors | `< >` | `< >` |
| `BL6-02` | Verify summary cards | Values match expected calculation | `< >` | `< >` |
| `BL6-03` | Verify allocation chart | Weights align with market value proportions | `< >` | `< >` |
| `BL6-04` | Verify trend chart | Trend endpoint data is rendered | `< >` | `< >` |
| `BL6-05` | Verify monthly realized PnL chart | Month entries and trade counts are correct | `< >` | `< >` |
| `BL6-06` | Export `summary` CSV | File downloaded, headers/data complete | `< >` | `< >` |
| `BL6-07` | Export `holdings` CSV | File downloaded, holdings rows correct | `< >` | `< >` |
| `BL6-08` | Export `trades` CSV | File downloaded, trades rows correct | `< >` | `< >` |
| `BL6-09` | Select a no-trade/no-holding portfolio | Empty-state shown cleanly | `< >` | `< >` |

---

## 8) BL-007: Strategy backtest skeleton

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `BL7-01` | Open `/strategies` page | Strategy/backtest page renders correctly | `< >` | `< >` |
| `BL7-02` | Create `moving_average` strategy | 201, strategy appears in list/select | `< >` | `< >` |
| `BL7-03` | Create `rsi` strategy | 201, RSI params persisted | `< >` | `< >` |
| `BL7-04` | Create `momentum` strategy | 201, momentum params persisted | `< >` | `< >` |
| `BL7-05` | Run backtest with valid inputs | Backtest status `completed`, id generated | `< >` | `< >` |
| `BL7-06` | View backtest list | New record visible with `return` and `trade_count` | `< >` | `< >` |
| `BL7-07` | Open backtest detail | Metrics present (`final_value`, `sharpe`, `drawdown`, `win_rate`) | `< >` | `< >` |
| `BL7-08` | Compare detail trades count vs summary trade_count | Counts are consistent | `< >` | `< >` |
| `BL7-09` | Check equity curve chart rendering | Curve appears with no runtime errors | `< >` | `< >` |
| `BL7-10` | Invalid date range (`start > end`) run | 400 validation error | `< >` | `< >` |
| `BL7-11` | Run with non-existent strategy_id | 404 `Strategy not found` | `< >` | `< >` |
| `BL7-12` | Reload page and reopen same backtest | Persisted result remains queryable | `< >` | `< >` |

---

## 9) Cross-BL Release Gate

| Case ID | Steps | Expected | Status | Evidence |
| --- | --- | --- | --- | --- |
| `GATE-01` | End-to-end smoke: create portfolio -> trade -> refresh quote -> analytics -> run backtest | Full critical path works without blocker | `< >` | `< >` |
| `GATE-02` | Re-run all automated checks | Backend tests + frontend lint/test/build all pass | `< >` | `< >` |
| `GATE-03` | Review unresolved defects | `P0=0`, `P1` within accepted threshold | `< >` | `< >` |

---

## 10) Defect Log

| Defect ID | Severity (`P0/P1/P2`) | Case ID | Summary | Status | Owner |
| --- | --- | --- | --- | --- | --- |
| `<BUG-001>` | `<P1>` | `<BLx-yy>` | `<summary>` | `<Open/Fixed/Verified>` | `<name>` |

---

## 11) Final Sign-off

- Go / No-Go: `<fill>`
- Residual risk: `<fill>`
- Follow-up actions: `<fill>`

| Role | Name | Date | Sign |
| --- | --- | --- | --- |
| QA/UAT | `<fill>` | `<YYYY-MM-DD>` | `< >` |
| Dev | `<fill>` | `<YYYY-MM-DD>` | `< >` |
| PM/Owner | `<fill>` | `<YYYY-MM-DD>` | `< >` |
