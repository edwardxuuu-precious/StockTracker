# StockTracker 全链路 UAT 验收清单（高价值收敛版）

Last updated: `2026-02-09`

## 1) Basic Info

| Field | Value |
| --- | --- |
| Project | `StockTracker` |
| Release Version | `<vX.Y.Z>` |
| Git Branch | `<branch>` |
| Commit / Tag | `<commit-or-tag>` |
| Environment | `Local` |
| Backend URL | `<http://localhost:<backend_port>>` |
| Frontend URL | `<http://localhost:5173>` |
| Tester | `<name>` |
| Test Date | `<YYYY-MM-DD>` |

## 2) Scope

### In Scope
- 本地数据闭环：行情下载、落库、查询、状态检查。
- 本地数据回测闭环：策略创建、回测执行、交易明细、结果一致性。
- Agent 闭环：自然语言生成策略、调参、报告、引用证据。
- 知识库闭环：PDF/TXT/JSON 入库、检索、治理策略、文档过滤。
- 运维闭环：调度器、发布门禁、回滚演练、回归烟测。
- 前端用户主路径：市场数据、策略回测、Agent、知识库、策略版本、组合分析页面。

### Out of Scope
- 云端部署端点真实打通（`OPS-003`，明确后续再做）。
- 交易所授权、商业化数据合规（当前阶段不阻塞个人研究验证）。

## 3) Entry Criteria（执行前必须满足）

- [ ] `backend/start-backend.cmd` 可启动，`.runtime/backend-port.txt` 存在。
- [ ] `frontend/start-frontend.cmd` 可启动并访问首页。
- [ ] `http://localhost:<backend_port>/docs` 可打开。
- [ ] 测试数据前缀已约定（建议统一 `UAT_YYYYMMDD_`）。
- [ ] 如执行调度器用例，`backend/config/ingestion_jobs.json` 已准备。
- [ ] 本轮验收的证据目录已创建（建议 `.runtime/uat/<run_id>/`）。

## 4) Test Data Plan

| Data ID | Purpose | Input | Expected Baseline |
| --- | --- | --- | --- |
| `TD-PF-01` | 组合/交易链路 | `UAT` 前缀组合，初始资金 `100000` | 可完成买卖与现金变动 |
| `TD-MD-CN-1M` | A 股分钟数据链路 | `600519`，`CN`，`1m`，近 1-2 日 | `status` 可见 bars 与区间 |
| `TD-MD-US-1D` | 美股日线链路 | `AAPL,MSFT`，`US`，`1d` | 回测最少可跑通一轮 |
| `TD-MD-US-1M` | 美股分钟链路（收盘后更新） | `AAPL`，`US`，`1m`，可用时间窗 | 若源支持则入库成功，否则给出明确错误 |
| `TD-KB-TXT` | 文本知识入库 | 风险控制短文（txt） | 检索命中并可引用 |
| `TD-KB-JSON` | 结构化知识入库 | 策略参数说明（json） | 检索时支持 source_type 过滤 |
| `TD-KB-PDF` | PDF 入库链路 | 研究报告片段（pdf） | 至少生成 1 个 chunk |

## 5) UAT Test Cases

执行说明：
- `Actual Result`、`Status`、`Evidence` 由执行者现场填写。
- `Status` 仅允许 `PASS / FAIL / BLOCKED`。

### A. 环境与启动

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-A-001` | Backend 启动与端口发现 | 1) 运行 `backend/start-backend.cmd` 2) 读取 `.runtime/backend-port.txt` 3) 访问 `/` 与 `/docs` | 后端启动成功；端口文件存在；`/` 返回 API 运行信息；`/docs` 可访问 |  |  |  |  |
| `UAT-A-002` | Frontend 启动与主导航 | 1) 运行 `frontend/start-frontend.cmd` 2) 打开首页 3) 依次点击 `Market Data/Strategies/Knowledge Base/Agent` | 页面均可打开且无阻塞错误 |  |  |  |  |
| `UAT-A-003` | API 路由可达性（核心域） | 使用 Swagger 或 API 客户端检查：`/api/v1/portfolios`、`/market-data/instruments`、`/backtests`、`/kb/documents`、`/agent/strategy/generate` | 所有核心路由可访问，非 5xx |  |  |  |  |
| `UAT-A-004` | 基线回归命令 | 运行 `python -m pytest backend/tests -q` | 全量后端用例通过（当前基线 `61 passed` 或更高） |  |  |  |  |

### B. 组合、交易、分析（用户资产主链路）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-B-001` | 创建组合 | 1) 在前端创建组合（初始资金 `100000`）2) 查看组合详情 | 组合创建成功；`cash_balance=initial_capital` |  |  |  |  |
| `UAT-B-002` | BUY/SELL 与持仓加权成本 | 1) 对同一标的执行两次 `BUY`（不同价格）2) 执行一次部分 `SELL` 3) 查看持仓与交易记录 | 持仓数量与加权成本正确；卖出后 `realized_pnl` 正确；现金变动正确 |  |  |  |  |
| `UAT-B-003` | 交易校验（负路径） | 发起 `SELL` 数量大于持仓数量 | 请求被拒绝（`400`）；错误信息清晰；数据不被污染 |  |  |  |  |
| `UAT-B-004` | 分析与导出 | 打开 `Analytics` 页面并导出 `summary/holdings/trades` CSV | 分析摘要字段完整；CSV 可下载，字段与时间戳合法 |  |  |  |  |

### C. 本地行情数据（核心依赖链路）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-C-001` | CN 1m 手动入库 | 调用 `POST /api/v1/market-data/ingest`：`symbols=["600519"]`,`market="CN"`,`interval="1m"` | 返回 `results`，状态为 `completed/partial`，无服务崩溃 |  |  |  |  |
| `UAT-C-002` | US 1d 手动入库 | 调用 `POST /api/v1/market-data/ingest`：`symbols=["AAPL","MSFT"]`,`market="US"`,`interval="1d"` | 至少 1 个标的成功入库；有 ingestion 记录 |  |  |  |  |
| `UAT-C-003` | US 1m 收盘后更新能力验证 | 收盘后调用 `POST /api/v1/market-data/ingest`：`symbols=["AAPL"]`,`market="US"`,`interval="1m"` | 支持时：入库成功并可查询；不支持时：明确失败原因且系统稳定 |  |  |  |  |
| `UAT-C-004` | 行情查询与状态诊断 | 调用 `/bars`、`/status`、`/ingestions` | 可返回 bars、时间区间、`gap_estimate` 与最近 ingestion 信息 |  |  |  |  |
| `UAT-C-005` | Provider 可替换性（接口层） | ingest 请求中切换 `provider` 参数（可用值与不可用值各一次） | 可用 provider 正常执行；不可用 provider 给出可理解错误，不影响其他流程 |  |  |  |  |

### D. 本地数据回测（关键业务价值）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-D-001` | 策略创建并触发回测 | 1) 创建策略（如 MA）2) 调用 `POST /api/v1/backtests/` 使用本地数据 | 返回 `201` 且 `status=completed`，`trade_count>0` |  |  |  |  |
| `UAT-D-002` | 回测结果一致性 | 查询 `/api/v1/backtests/{id}` 与 `/trades` | 指标齐全（`total_return/sharpe/max_drawdown/win_rate`）；`is_simulated=false`；终值与权益曲线末值一致 |  |  |  |  |
| `UAT-D-003` | 回测参数校验（负路径） | 提交 `start_date > end_date` 或不存在的 `strategy_id` | 分别返回 `400/404`；不产生脏回测记录 |  |  |  |  |
| `UAT-D-004` | 跨市场回测映射 | 在 `parameters` 中提供 `markets` 字典（如 `AAPL:US`、`600519:CN`）并运行 | 可按 symbol 维度解析市场；无“多市场冲突”误判 |  |  |  |  |

### E. Agent、聊天与策略版本（智能闭环）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-E-001` | 自然语言生成策略脚本 | 调用 `POST /api/v1/agent/strategy/generate`，`save_strategy=true` | 返回 `code`、参数与策略实体；策略可在列表中看到 |  |  |  |  |
| `UAT-E-002` | Agent 调参并产出最优试验 | 调用 `POST /api/v1/agent/strategy/tune`（设置 `parameter_grid/max_trials/top_k`） | 返回 `best_trial/top_trials`；每个 trial 对应有效 `backtest_id` |  |  |  |  |
| `UAT-E-003` | Agent 报告（定量+定性） | 调用 `POST /api/v1/agent/backtests/{id}/report` | 报告包含 `quantitative_recommendations` 与 `qualitative_recommendations` |  |  |  |  |
| `UAT-E-004` | Chat 会话到策略落地 | 1) `POST /api/v1/chat/sessions` 2) 发送包含策略意图的消息 3) 查看返回与策略列表 | 会话可持续；assistant 回复；可自动创建策略（含版本快照） |  |  |  |  |
| `UAT-E-005` | 策略版本管理与对比 | 1) 查看 `/strategies/{id}/versions` 2) 创建快照 3) 调用 `/strategies/versions/compare` | 版本号递增；对比返回 backtest 统计与最佳指标 |  |  |  |  |

### F. 知识库检索与治理（Agent 证据基础）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-F-001` | 多类型知识入库 | 分别调用 `POST /api/v1/kb/ingest` 上传 `pdf/txt/json`，再调用 `GET /api/v1/kb/documents` | 三类文档均可入库且文档列表可见 |  |  |  |  |
| `UAT-F-002` | 检索模式完整性 | 用同一 query 依次调用 `POST /api/v1/kb/search`：`fts/vector/hybrid` | 三种模式均有结构化返回；命中包含 `reference_id/confidence/snippet` |  |  |  |  |
| `UAT-F-003` | 治理策略与过滤 | 检索时测试 `policy_profile`、`allowed_source_types`、`blocked_source_keywords`、`allow_fallback` | 严格模式下文档集中度降低；过滤规则生效；关闭 fallback 时低相关查询可返回空 |  |  |  |  |
| `UAT-F-004` | Agent 报告引用治理 | 生成报告时指定 `citation_policy_profile` 与 source 过滤参数 | `citations` 与治理参数一致；flags 合理，无越权来源 |  |  |  |  |

### G. 调度器与可观测性（持续更新能力）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-G-001` | 调度器单轮执行 | 设 `SCHEDULER_RUN_ONCE=true` 后运行 `python backend/run_scheduler.py` | 至少执行一轮并正常退出 |  |  |  |  |
| `UAT-G-002` | 心跳与周期报告 | 检查 `.runtime/scheduler/heartbeat.json` 与 `.runtime/scheduler/reports/cycle_*.json` | 心跳包含状态与时间；周期报告包含 jobs/symbol 成功失败统计 |  |  |  |  |
| `UAT-G-003` | 幂等重复执行 | 同一 job 连续执行两轮后检查 bars 与 ingest 日志 | bars 不重复膨胀；日志可追踪两次执行 |  |  |  |  |
| `UAT-G-004` | 告警钩子健壮性 | 设置 `SCHEDULER_ALERT_WEBHOOK` 为测试地址并构造失败任务 | 失败时触发 webhook；失败不会拖垮调度主循环 |  |  |  |  |

### H. 发布治理、回滚与安全基线（上线前必须）

| Case ID | Scenario | Steps | Expected Result | Actual Result | Status | Evidence | Defect ID |
| --- | --- | --- | --- | --- | --- | --- | --- |
| `UAT-H-001` | Release gate（dev） | 运行 `python backend/scripts/release_gate.py --profile dev --skip-docker --allow-dirty-git` | Gate 通过并产出 `.runtime/release_gate_*.json` |  |  |  |  |
| `UAT-H-002` | KB 阈值门禁联动 | 运行 `release_gate.py` 并附带 `--kb-policy backend/config/kb_benchmark_policy.json` | KB benchmark 按策略执行；阈值判断可审计 |  |  |  |  |
| `UAT-H-003` | 回滚演练 | 运行 `python backend/scripts/rollback_drill.py --env staging` | 生成演练摘要与 deploy 报告；退出码成功 |  |  |  |  |
| `UAT-H-004` | 生产安全最小门槛 | 在 `APP_ENV=production` 场景验证非默认 `SECRET_KEY` 要求 | 默认占位密钥被拒绝；自定义密钥可启动 |  |  |  |  |

## 6) Defect Log

| Defect ID | Severity (`P0/P1/P2`) | Summary | Repro Steps | Impact | Owner | Status |
| --- | --- | --- | --- | --- | --- | --- |
| `<BUG-001>` | `<P1>` | `<summary>` | `<steps>` | `<impact>` | `<name>` | `<Open/Fixed/Verified>` |

## 7) Exit Criteria

- [ ] 所有 in-scope 用例已执行并记录证据。
- [ ] `P0 = 0`。
- [ ] `P1` 达到阈值要求（见下）。
- [ ] 核心回归命令通过（至少 backend 全量 tests + dev release gate）。
- [ ] 关键链路均至少一次 `PASS`：`数据入库 -> 回测 -> Agent 报告 -> 引用证据`。

Acceptance threshold for `P1`:
- `P1 <= 2` 且每个 `P1` 均有明确 workaround 和修复计划。

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

