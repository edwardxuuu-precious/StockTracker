# StockTracker Real Usage Log (2026-02)

Last updated: `2026-02-10`

## 1) Basic Info

| Field | Value |
| --- | --- |
| Project | `StockTracker` |
| Environment | `Local` |
| Backend URL | `http://localhost:8001` |
| Frontend URL | `http://localhost:5173` |
| Owner | `<name>` |
| Month | `2026-02` |

## 2) Run Rule

- 每次操作必须记录：输入、输出、耗时、异常。
- 若出现异常，先记录证据路径，再决定是否提缺陷。
- 缺陷统一追加到：`docs/QA/UAT_FullChain_Defects_2026-02-09.md`。

## 3) Day 1 Script (Data -> Backtest -> Agent -> Version)

| ID | Scenario | Steps | Expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `RU-D1-01` | 数据更新（CN/US） | 1) 执行 `POST /api/v1/market-data/ingest`（`CN 1m` + `US 1d`） 2) 查询 `/status` 与 `/ingestions` | 入库请求成功；状态可查询；日志可追踪 | `CN 1m completed=1, total_bars=241; US 1d completed=2, total_bars(AAPL)=276` | `PASS` | `.runtime/real_usage/20260210_095317/RU-D1-01_evidence.json` |
| `RU-D1-02` | 本地数据回测 | 1) 选现有策略或新建策略 2) 执行 `POST /api/v1/backtests/` 3) 查询 `/backtests/{id}` | `status=completed`；有交易明细；指标完整 | `backtest_id=25, status=completed, trade_count=4, total_return=-1.3095, sharpe=-1.2584` | `PASS` | `.runtime/real_usage/20260210_095756/RU-D1-02_evidence.json` |
| `RU-D1-03` | Agent 报告 | 1) 调用 `POST /api/v1/agent/backtests/{id}/report` 2) 检查定量/定性建议 | 接口 `200`；建议可读；引用链路正常 | `status=200, quantitative=2, qualitative=2, citations=3, markdown_length=1559` | `PASS` | `.runtime/real_usage/20260210_095833/RU-D1-03_evidence.json` |
| `RU-D1-04` | 策略版本快照 | 1) `POST /api/v1/strategies/{id}/versions` 2) `POST /api/v1/strategies/versions/compare` | 版本可新增；对比可返回统计 | `strategy_id=17, versions 1->2, compare_count=2` | `PASS` | `.runtime/real_usage/20260210_095908/RU-D1-04_evidence.json` |

## 4) Day 2 Script (KB -> Retune -> Compare -> Review)

| ID | Scenario | Steps | Expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `RU-D2-01` | 知识库新增资料 | 1) 上传 `pdf/txt/json` 到 KB 2) `POST /api/v1/kb/search` 三种模式验证 | 文档可见；检索有命中 | `uploaded_docs=3(ids=13/14/15), visible=3, fts_hits=2(match=2), vector_hits=8(match=3), hybrid_hits=8(match=3)` | `PASS` | `.runtime/real_usage/20260210_101228/RU-D2-01_evidence.json` |
| `RU-D2-02` | 基于新资料再次调参 | 1) 执行 `POST /api/v1/agent/strategy/tune` 2) 生成新报告 | 产生可用 `best_trial`；报告有建议与证据 | `best_backtest_id=29, best_params(short=3,long=10,alloc=0.2), report quantitative=2, qualitative=2, citations=5` | `PASS` | `.runtime/real_usage/20260210_101404/RU-D2-02_evidence.json` |
| `RU-D2-03` | 新旧版本对比 | 1) 比较 Day1 与 Day2 版本 2) 比较回测指标差异 | 指标变化可解释，结果可复现 | `strategy_id=17, versions 2->3(id 23->24), delta_return=+0.6752, delta_sharpe=+0.3587, delta_drawdown=-1.1017` | `PASS` | `.runtime/real_usage/20260210_101454/RU-D2-03_evidence.json` |
| `RU-D2-04` | 复盘结论 | 记录本轮最有效参数、失效条件、下轮行动 | 形成可执行下一步计划 | `effective_params=(short=3,long=10,alloc=0.2), negatives=(return<0,sharpe<0), actions=4` | `PASS` | `.runtime/real_usage/20260210_101551/RU-D2-04_evidence.json` |

### Day 3 Script (Wide Window -> Conservative Variant -> Compare -> Report)

| ID | Scenario | Steps | Expected | Actual | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `RU-D3-01` | 宽窗口多市场数据更新 | 1) `POST /api/v1/market-data/ingest` for `US(AAPL/MSFT/NVDA) 1d` + `CN(600519/000001) 1d` 2) 验证结果状态 | 各市场至少 1 个标的入库成功；接口稳定 | `US completed=3(ingested=90 each), CN completed=2(ingested=87 each)` | `PASS` | `.runtime/real_usage/20260210_102151/RU-D3-01_evidence.json` |
| `RU-D3-02` | 保守参数策略变体 | 创建新策略（更低仓位、更长均线） | 变体策略可创建并可用于回测 | `strategy_id=18, name=RU_D3_Conservative_MA_20260210_102151` | `PASS` | `.runtime/real_usage/20260210_102151/RU-D3-02_evidence.json` |
| `RU-D3-03` | 基线 vs 变体跨市场对比 | 对 `AAPL/MSFT/600519` 在同窗回测基线与变体，并对比指标 | 两次回测均完成；可得到可解释指标差异 | `baseline id=31 vs variant id=32; delta_return=+2.1371, delta_sharpe=+0.3942, delta_drawdown=-3.0572, delta_trade_count=-10` | `PASS` | `.runtime/real_usage/20260210_102151/RU-D3-03_evidence.json` |
| `RU-D3-04` | Agent 报告与复盘 | 对变体回测生成报告并输出复盘结论 | 报告含定量/定性建议与引用；复盘文件可追溯 | `report status=200, quantitative=2, qualitative=2, citations=5` | `PASS` | `.runtime/real_usage/20260210_102151/RU-D3-04_evidence.json` |

## 5) Operation Log (Record Every Action)

| Timestamp | Scenario ID | Input (Parameters / Prompt) | Output (Key Metrics / Conclusion) | Duration | Exception | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `2026-02-10 09:53:17` | `RU-D1-01` | `CN: 600519 1m, lookback=1d; US: AAPL/MSFT 1d, lookback=30d` | `CN ingest completed=1; US ingest completed=2; status/ingestions query success` | `18.43s` | `none` | `.runtime/real_usage/20260210_095317/RU-D1-01_evidence.json` |
| `2026-02-10 09:54:19` | `RU-D1-02` | `AAPL/MSFT, 2026-01-01~2026-02-10, initial_capital=100000` | `request failed before backtest run` | `4.15s` | `Unable to connect to the remote server` | `.runtime/real_usage/20260210_095419/RU-D1-02_evidence.json` |
| `2026-02-10 09:57:56` | `RU-D1-02` | `AAPL/MSFT, 2026-01-01~2026-02-10, initial_capital=100000` | `backtest_id=25, status=completed, trade_count=4` | `2.21s` | `none` | `.runtime/real_usage/20260210_095756/RU-D1-02_evidence.json` |
| `2026-02-10 09:58:33` | `RU-D1-03` | `backtest_id=25, top_k_sources=3` | `report generated, quantitative=2, qualitative=2, citations=3` | `2.13s` | `none` | `.runtime/real_usage/20260210_095833/RU-D1-03_evidence.json` |
| `2026-02-10 09:59:08` | `RU-D1-04` | `strategy_id=17` | `snapshot created, versions 1->2, compare_count=2` | `2.18s` | `none` | `.runtime/real_usage/20260210_095908/RU-D1-04_evidence.json` |
| `2026-02-10 10:11:34` | `RU-D2-01` | `ingest: uat_kb_note json/txt/pdf (first attempt)` | `json ingest failed; search validation not met` | `0.28s` | `Unexpected UTF-8 BOM (decode using utf-8-sig)` | `.runtime/real_usage/20260210_101134/RU-D2-01_evidence.json` |
| `2026-02-10 10:12:29` | `RU-D2-01` | `ingest: ru_d2_01_kb_note_20260210_101228.(txt/json/pdf); query='silver fox risk protocol max drawdown guard allocation throttle'` | `uploaded=3, visible=3, fts/vector/hybrid matched_uploaded=2/3/3` | `0.27s` | `none` | `.runtime/real_usage/20260210_101228/RU-D2-01_evidence.json` |
| `2026-02-10 10:14:04` | `RU-D2-02` | `strategy_id=17, symbols=AAPL/MSFT, 2026-01-01~2026-02-10, max_trials=5` | `best_backtest_id=29, best_params=(3,10,0.2), report q/qual/citations=2/2/5` | `0.13s` | `none` | `.runtime/real_usage/20260210_101404/RU-D2-02_evidence.json` |
| `2026-02-10 10:14:55` | `RU-D2-03` | `strategy_id=17, snapshot note=RU-D2-03 snapshot after retune backtest=29` | `versions 2->3; backtest delta return/sharpe/drawdown=+0.6752/+0.3587/-1.1017` | `0.18s` | `none` | `.runtime/real_usage/20260210_101454/RU-D2-03_evidence.json` |
| `2026-02-10 10:15:51` | `RU-D2-04` | `synthesize RU-D2-02/03 into review conclusions` | `effective params + failure conditions + 4 next actions documented` | `0.05s` | `none` | `.runtime/real_usage/20260210_101551/RU-D2-04_evidence.json` |
| `2026-02-10 10:20:51` | `RU-D3-01` | `first attempt of Day3 pipeline` | `command timeout before full completion` | `14.00s` | `command timed out` | `.runtime/real_usage/20260210_102051/d301_ingest_US.json` |
| `2026-02-10 10:21:56` | `RU-D3-01` | `US: AAPL/MSFT/NVDA 1d + CN: 600519/000001 1d, 2025-10-01~2026-02-10` | `US completed=3, CN completed=2` | `~8.00s` | `none` | `.runtime/real_usage/20260210_102151/RU-D3-01_evidence.json` |
| `2026-02-10 10:21:58` | `RU-D3-02` | `create conservative MA variant(short=4,long=14,alloc=0.15)` | `strategy_id=18 created` | `~0.10s` | `none` | `.runtime/real_usage/20260210_102151/RU-D3-02_evidence.json` |
| `2026-02-10 10:22:01` | `RU-D3-03` | `run baseline(strategy=17) and variant(strategy=18) on AAPL/MSFT/600519` | `backtest 31/32 completed; variant drawdown improved` | `~3.70s` | `none` | `.runtime/real_usage/20260210_102151/RU-D3-03_evidence.json` |
| `2026-02-10 10:22:02` | `RU-D3-04` | `generate report for backtest_id=32 with top_k_sources=5` | `q/qual/citations=2/2/5; review markdown generated` | `~0.20s` | `none` | `.runtime/real_usage/20260210_102151/RU-D3-04_evidence.json` |
| `<YYYY-MM-DD HH:mm:ss>` | `<RU-Dx-xx>` | `<input>` | `<output>` | `<mm:ss>` | `<none / message>` | `<file/path>` |

## 6) Day Summary

### Day 1 Summary

| Item | Value |
| --- | --- |
| Completed | `4/4` |
| New Defects | `0` |
| Blocking Issue | `no` |
| Next Action | `Start Day 2 with RU-D2-01 (ingest new KB materials and verify search modes).` |

### Day 2 Summary

| Item | Value |
| --- | --- |
| Completed | `4/4` |
| New Defects | `0` |
| Blocking Issue | `no` |
| Next Action | `Day 2 completed. Start next cycle with wider symbol/time coverage and drawdown-guard strategy variant.` |

### Day 3 Summary

| Item | Value |
| --- | --- |
| Completed | `4/4` |
| New Defects | `0` |
| Blocking Issue | `no` |
| Next Action | `Continue real usage on longer horizon and track if variant can turn total_return/sharpe positive.` |

## 7) Quick Commands

- Backend tests: `python -m pytest backend/tests -q`
- Agent flow tests: `python -m pytest backend/tests/test_agent_and_versions_api.py -q`
- Market data tests: `python -m pytest backend/tests/test_market_data_api.py -q`
