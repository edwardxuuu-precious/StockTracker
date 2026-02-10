# StockTracker 全链路 UAT 执行记录（Run 1）

Run ID: `20260209_195743`  
Checklist baseline: `docs/QA/UAT_FullChain_Checklist_2026-02-09.md`

## 汇总

- Total cases executed: `34`
- `PASS`: `34`
- `FAIL`: `0`
- `BLOCKED`: `0`

## 执行结果汇总

| Case ID | Status | Actual Result (Summary) | Evidence |
| --- | --- | --- | --- |
| `UAT-A-001` | `PASS` | 后端已可用，端口文件存在，`/` 与 `/docs` 均返回 `200`。 | `.runtime/uat/20260209_195743/UAT-A-001_result.json` |
| `UAT-A-002` | `PASS` | 前端 `5173` 可访问，`/`、`/market-data`、`/strategies`、`/knowledge-base`、`/chat` 路由均 `200` 且页面主区域加载成功。 | `.runtime/uat/20260209_195743/UAT-A-002_result.json` |
| `UAT-A-003` | `PASS` | 核心 API 路由可达：`portfolios`、`market-data/instruments`、`backtests`、`kb/documents`、`agent/strategy/generate` 均返回 `200`。 | `.runtime/uat/20260209_195743/UAT-A-003_result.json` |
| `UAT-A-004` | `PASS` | 后端全量测试通过，最新回归结果 `62 passed in 10.45s`。 | `.runtime/uat/20260209_195743/UAT-A-004_result.json`, `.runtime/uat/20260209_195743/UAT-A-004_pytest.log` |
| `UAT-B-001` | `PASS` | 组合创建成功，`initial_capital=100000` 且 `cash_balance=100000`；前端详情页可见组合名与资金显示。 | `.runtime/uat/20260209_195743/UAT-B-001_result.json` |
| `UAT-B-002` | `PASS` | 买卖流程与交易明细校验通过：加权成本 `107`、卖出已实现盈亏 `22`、现金余额 `808`。 | `.runtime/uat/20260209_195743/UAT-B-002_result.json` |
| `UAT-B-003` | `PASS` | 卖出超持仓返回 `400`，且持仓数量、现金余额均保持不变。 | `.runtime/uat/20260209_195743/UAT-B-003_result.json` |
| `UAT-B-004` | `PASS` | 分析接口可用，`summary/holdings/trades` 三类 CSV 导出成功并含关键列。 | `.runtime/uat/20260209_195743/UAT-B-004_result.json`, `.runtime/uat/20260209_195743/UAT-B-004_*.csv` |
| `UAT-C-001` | `PASS` | CN `600519` `1m` 手动入库成功，`ingested=93`。 | `.runtime/uat/20260209_195743/UAT-C-001_result.json` |
| `UAT-C-002` | `PASS` | US `AAPL/MSFT` `1d` 入库均成功，均为 `completed`。 | `.runtime/uat/20260209_195743/UAT-C-002_result.json` |
| `UAT-C-003` | `PASS` | US `AAPL` `1m` 收盘后更新请求可执行，返回 `completed`（本轮 `ingested=0`）。 | `.runtime/uat/20260209_195743/UAT-C-003_result.json` |
| `UAT-C-004` | `PASS` | `bars/status/ingestions` 查询链路可用（本轮 `600519 CN 1m` 查询成功）。 | `.runtime/uat/20260209_195743/UAT-C-004_result.json` |
| `UAT-C-005` | `PASS` | provider 可替换验证通过：`yfinance` 成功；无效 provider 返回清晰失败信息。 | `.runtime/uat/20260209_195743/UAT-C-005_result.json` |
| `UAT-D-001` | `PASS` | 本地数据回测成功，`status=completed`，`trade_count=12`。 | `.runtime/uat/20260209_195743/UAT-D-001_result.json` |
| `UAT-D-002` | `PASS` | 复测通过：`final_value` 与 `equity_curve` 末值一致（`101854.1066`）。 | `.runtime/uat/20260209_195743/UAT-D-002_result.json` |
| `UAT-D-003` | `PASS` | 负路径校验通过：无效日期返回 `400`，不存在策略返回 `404`。 | `.runtime/uat/20260209_195743/UAT-D-003_result.json` |
| `UAT-D-004` | `PASS` | 跨市场映射回测执行成功（`AAPL:US` + `600519:CN`），`status=completed`。 | `.runtime/uat/20260209_195743/UAT-D-004_result.json` |
| `UAT-E-001` | `PASS` | Agent 可生成可保存策略脚本，返回策略实体与参数。 | `.runtime/uat/20260209_195743/UAT-E-001_result.json` |
| `UAT-E-002` | `PASS` | Agent 调参成功，返回 `best_trial/top_trials`，并关联有效 `backtest_id`。 | `.runtime/uat/20260209_195743/UAT-E-002_result.json` |
| `UAT-E-003` | `PASS` | 复测通过：报告接口返回 `200`，定量/定性建议均返回。 | `.runtime/uat/20260209_195743/UAT-E-003_result.json` |
| `UAT-E-004` | `PASS` | Chat 会话可创建并返回 assistant 响应，且可自动创建策略。 | `.runtime/uat/20260209_195743/UAT-E-004_result.json` |
| `UAT-E-005` | `PASS` | 策略版本快照与版本对比可用，版本数可递增。 | `.runtime/uat/20260209_195743/UAT-E-005_result.json` |
| `UAT-F-001` | `PASS` | 复测通过：JSON 入库 `chunk_count=1`（UTF-8 无 BOM 测试数据）。 | `.runtime/uat/20260209_195743/UAT-F-001_result.json` |
| `UAT-F-002` | `PASS` | `fts/vector/hybrid` 三种检索模式均返回命中。 | `.runtime/uat/20260209_195743/UAT-F-002_result.json` |
| `UAT-F-003` | `PASS` | 复测通过：`allowed_source_types=json` 与 `allow_fallback=false` 行为符合预期。 | `.runtime/uat/20260209_195743/UAT-F-003_result.json`, `.runtime/uat/20260209_195743/UAT_retest_P1.json` |
| `UAT-F-004` | `PASS` | 复测通过：Agent 报告引用治理场景返回 `200`，过滤生效。 | `.runtime/uat/20260209_195743/UAT-F-004_result.json` |
| `UAT-G-001` | `PASS` | 调度器 `run-once` 可执行并完成一轮任务。 | `.runtime/uat/20260209_195743/UAT-G-001_result.json` |
| `UAT-G-002` | `PASS` | 心跳与周期报告文件按预期生成。 | `.runtime/uat/20260209_195743/UAT-G-002_result.json`, `.runtime/uat/20260209_195743/g_heartbeat.json`, `.runtime/uat/20260209_195743/g_reports/` |
| `UAT-G-003` | `PASS` | 同一任务重复执行未导致 bars 重复增长（幂等性通过）。 | `.runtime/uat/20260209_195743/UAT-G-003_result.json` |
| `UAT-G-004` | `PASS` | 构造失败任务后 webhook 成功接收告警事件。 | `.runtime/uat/20260209_195743/UAT-G-004_result.json`, `.runtime/uat/20260209_195743/g_webhook/received.json` |
| `UAT-H-001` | `PASS` | `dev` 发布门禁执行通过并产生日志证据。 | `.runtime/uat/20260209_195743/UAT-H-001_result.json`, `.runtime/uat/20260209_195743/UAT-H-001_release_gate_dev.log` |
| `UAT-H-002` | `PASS` | `prod` + `kb-policy` 门禁执行通过，KB 阈值链路可运行。 | `.runtime/uat/20260209_195743/UAT-H-002_result.json`, `.runtime/uat/20260209_195743/UAT-H-002_release_gate_prod_kb_policy.log` |
| `UAT-H-003` | `PASS` | 回滚演练命令执行通过并留存演练日志。 | `.runtime/uat/20260209_195743/UAT-H-003_result.json`, `.runtime/uat/20260209_195743/UAT-H-003_rollback_drill.log` |
| `UAT-H-004` | `PASS` | 生产密钥安全校验通过（`test_security_config.py` 通过）。 | `.runtime/uat/20260209_195743/UAT-H-004_result.json`, `.runtime/uat/20260209_195743/UAT-H-004_security.log` |

## 备注

- 前端运行中观察到 React Router future warning（非阻塞，不影响本轮验收结论）。
- 初始失败项已完成复测并关闭，复测证据：`.runtime/uat/20260209_195743/UAT_retest_P1.json`。
