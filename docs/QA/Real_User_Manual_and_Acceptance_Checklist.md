# StockTracker 真实用户视角项目手册与引导式验收清单

- 文档位置: `docs/QA/Real_User_Manual_and_Acceptance_Checklist.md`
- 适用版本: 当前仓库 `main` 分支（截至 2026-02-10）
- 目标: 用一份文档完成项目介绍、使用教程、功能验收、预期效果与实现原理说明
- 验收基线:
  - `venv\Scripts\python -m pytest backend/tests -q` -> `86 passed`
  - `cd frontend && npm run lint` -> 通过
  - `cd frontend && npm run test:unit` -> 通过

---

## 0. 如何使用这份文档

按下面顺序执行即可：

1. 先做「第 3 章 启动与基础检查」。
2. 再做「第 4 章 从零到一完整使用教程」。
3. 最后按「第 5 章 引导式功能验收清单」逐项打勾。
4. 若遇到不一致，参考「第 7 章 已知问题与验收口径」。

---

## 1. 项目介绍（真实用户视角）

### 1.1 这个系统能解决什么问题

StockTracker 是一个面向个人投资/量化策略验证的本地化系统，核心目标是把下面几件事连成一条闭环：

1. 组合管理: 建组合、看持仓、执行买卖、看现金和收益变化。
2. 策略管理: 建策略、调参数、跑回测、看收益曲线和交易明细。
3. 数据管理: 把市场行情入库，做数据健康检查，避免“无数据回测”。
4. 知识与 AI: 导入知识库材料，支持检索、Agent 生成策略、自动调参、生成复盘报告。

### 1.2 典型用户旅程

1. 创建组合并录入初始持仓。
2. 执行买卖，观察持仓和现金变化。
3. 进入分析页查看收益拆解并导出 CSV。
4. 新建策略并跑回测。
5. 用 Agent 做自动调参，拿到最优试验。
6. 让 Agent 结合知识库生成复盘建议。

### 1.3 系统边界（你需要提前知道）

1. 回测依赖本地行情库，不会自动从外网拉齐缺失数据。
2. Agent 能力依赖 LLM 配置；若强制要求 LLM 但没配置，后端会在启动阶段失败。
3. 报价、行情拉取依赖外部数据源，网络不稳定时会出现降级行为。

---

## 2. 系统结构与功能地图

### 2.1 架构总览（通俗版）

1. 前端: React + Vite（页面交互层）。
2. 后端: FastAPI（业务逻辑与 API）。
3. 存储: SQLite（组合、策略、回测、知识库、行情数据）。
4. 外部能力:
   - 行情/报价: `yfinance` / `stooq` / `akshare`
   - LLM: DeepSeek 或 OpenRouter（通过 OpenAI SDK 兼容接口）

### 2.2 前端页面与后端能力映射

| 前端页面 | 路由 | 主要后端接口 |
| --- | --- | --- |
| 首页 | `/` | 无核心写操作 |
| 组合列表 | `/portfolios` | `GET/POST/PUT/DELETE /api/v1/portfolios` |
| 组合详情 | `/portfolios/:id` | `.../trades`, `.../holdings`, `GET /api/v1/quotes/*` |
| 组合编辑 | `/portfolios/:id/edit` | `PUT /portfolios/{id}`, `POST/DELETE holdings` |
| 数据分析 | `/analytics` | `GET /api/v1/analytics/portfolios/{id}` + `.../export` |
| 策略回测 | `/strategies` | `GET/POST/PUT /api/v1/strategies`, `POST/GET /api/v1/backtests` |
| 版本对比 | `/strategy-versions` | `GET/POST /strategies/{id}/versions`, `POST /strategies/versions/compare` |
| 市场数据 | `/market-data` | `GET /status`, `GET /ingestions`, `POST /ingest` |
| 知识库 | `/knowledge-base` | `POST /kb/ingest`, `/kb/ingest-text`, `/kb/search`, `GET /kb/documents` |
| Agent 工作台 | `/chat` | `agent/*` + `chat/*` |

### 2.3 关键数据实体（你在验收时会看到）

1. Portfolio: 组合主信息（初始资金、现金余额、当前总值、是否启用）。
2. Holding: 某股票持仓（数量、均价、当前价、市值、浮盈亏）。
3. PortfolioTrade: 组合实盘交易记录（BUY/SELL、成交额、已实现盈亏）。
4. Strategy: 策略定义（类型、参数、代码）。
5. StrategyVersion: 策略快照版本（可比较）。
6. Backtest + Trade: 回测任务与回测交易明细。
7. Market Data: Instrument + Bars(1m/1d) + ingestion logs。
8. KB: 文档、分块、检索命中。

---

## 3. 启动与基础检查（先做）

## 3.1 推荐启动方式（Windows）

在仓库根目录运行：

```bat
start-all.cmd
```

预期效果：

1. 自动拉起两个窗口（Backend / Frontend）。
2. 后端端口写入 `.runtime/backend-port.txt`。
3. 前端自动读取该端口并设置 `VITE_API_URL`。

## 3.2 手动启动方式

1. 后端:

```bat
backend\start-backend.cmd
```

2. 前端:

```bat
frontend\start-frontend.cmd
```

3. （可选）调度器:

```bat
backend\start-scheduler.cmd
```

## 3.3 Docker 启动（可选）

```bash
docker-compose up --build
```

默认端口：

1. Backend: `8001`
2. Frontend: `5173`

## 3.4 启动后最小健康检查

1. 打开后端文档: `http://localhost:<后端端口>/docs`
2. 打开前端: `http://localhost:<前端端口>/`
3. 调接口 smoke test:

```bash
curl http://localhost:<后端端口>/api/v1/portfolios/
```

预期: HTTP 200，返回数组（初始可为空）。

---

## 4. 从零到一完整使用教程（带“你应该看到什么”）

## 4.1 创建第一个组合

操作路径：`组合管理 -> 创建组合`

推荐输入：

1. 名称: `UAT_Demo_Portfolio`
2. 初始资金: `100000`
3. 初始持仓可先留空

预期效果：

1. 创建成功后跳转到组合详情页。
2. 组合当前总值 = 初始资金；现金余额 = 初始资金。

实现原理（通俗）：

1. 后端创建组合时，`cash_balance` 与 `current_value` 初始等于 `initial_capital`。
2. `current_value` 实时按 `现金 + 持仓市值汇总`计算。

## 4.2 执行一笔 BUY 交易

操作路径：组合详情页「交易执行」。

示例输入：

1. 方向: BUY
2. 代码: `AAPL`
3. 数量: `10`
4. 成交价: `150`
5. 手续费: `1`

预期效果：

1. 交易记录新增一行 BUY。
2. 现金余额减少 `10*150 + 1`。
3. 持仓新增 AAPL，均价按加权成本维护。

实现原理：

1. 买入校验代码格式并尝试报价源验证。
2. 成本按 `数量*价格 + 手续费`计入持仓成本。
3. 相同 symbol 会合并成一条持仓（避免重复行）。

## 4.3 执行一笔 SELL 交易

示例输入：

1. 方向: SELL
2. 代码: `AAPL`
3. 数量: `5`
4. 成交价: `160`
5. 手续费: `1`

预期效果：

1. 交易记录新增 SELL。
2. `realized_pnl` 按公式变化并可见。
3. 持仓数量减少；若卖完，持仓条目消失。

实现原理：

1. 已实现盈亏 = `(卖价 - 持仓均价)*卖出数量 - 手续费`。
2. 卖出不再做外部报价验证（已有持仓即可卖）。

## 4.4 刷新实时报价

操作路径：组合详情页「持仓明细 -> 刷新报价」。

预期效果：

1. 当前价、市值、浮盈亏更新。
2. 报价暂时不可用时，系统保留缓存价格并给出提示，不会直接清空表格。

实现原理：

1. 报价服务有内存 TTL 缓存。
2. provider 链路失败时会回退到最近缓存值。

## 4.5 进入数据分析并导出报表

操作路径：`数据分析`

操作：

1. 选择组合。
2. 查看 summary / 趋势 / 持仓分布 / 月度已实现收益。
3. 分别导出 `summary` / `holdings` / `trades` CSV。

预期效果：

1. 总资产、总收益、已实现/未实现收益一致。
2. CSV 文件名形如 `portfolio_<id>_<report>.csv`。
3. 时间字段为 UTC ISO 格式（`...Z`）。

实现原理：

1. 分析页数据来自后端聚合计算。
2. 导出端点直接服务端生成 CSV。

## 4.6 创建策略并运行回测

操作路径：`交易策略`

步骤：

1. 新建策略（如均线策略 short=5, long=20）。
2. 在回测表单选择策略、symbol、日期区间、资金参数。
3. 提交回测。

预期效果：

1. 回测任务状态为 `completed`（成功时）。
2. 可查看关键指标: `total_return`、`sharpe_ratio`、`max_drawdown`、`win_rate`。
3. 可查看收益曲线与交易明细。

实现原理：

1. 回测引擎读取本地 bars 数据，不从外部实时拉取。
2. 每个 symbol 默认单持仓模型；结束时强制平仓以稳定统计口径。

## 4.7 管理策略版本并对比

操作路径：`版本对比`

步骤：

1. 选择策略。
2. 创建快照。
3. 选择至少 2 个版本执行对比。

预期效果：

1. 看到版本号、创建人、创建时间。
2. 对比结果有 backtest_count、best_total_return、best_sharpe_ratio。

实现原理：

1. 每次策略创建/更新会自动生成版本快照。
2. 版本对比基于 `strategy_version_id` 关联回测记录汇总。

## 4.8 市场数据入库与健康检查

操作路径：`市场数据`

步骤：

1. 先执行“手动入库”（symbol/market/interval）。
2. 再执行“数据健康检查”。
3. 查看“入库日志”。

预期效果：

1. 入库结果显示每个 symbol 的 `status` 和 `ingested`。
2. 健康检查显示总 bar 数、起止时间、gap_estimate、最后入库状态。
3. 日志表有对应 completed/failed 记录。

实现原理：

1. service 将外部 bars upsert 到本地表（按 `instrument_id+ts+source` 去重更新）。
2. DataSourceMeta 记录最后成功时间和错误信息。

## 4.9 知识库导入与检索

操作路径：`知识库`

步骤：

1. 上传文件（pdf/txt/json）或直接保存文本。
2. 用 `hybrid` 模式检索关键词。
3. 观察命中分数、片段、来源文档。

预期效果：

1. ingest 返回 chunk_count > 0。
2. search 返回 hits，且含 `reference_id`、`confidence`、`governance_flags`。

实现原理：

1. 文档分块 + 哈希向量 embedding + SQLite FTS。
2. `hybrid` 会融合 vector/fts/术语重合/新鲜度分数并做治理裁剪。

## 4.10 Agent 生成、调参与复盘报告

操作路径：`AI 助手`（`/chat` 页面中的 Agent 工作台）

步骤：

1. 提示词生成策略（可勾选保存）。
2. 对策略执行自动调参。
3. 使用 best trial 的 backtest_id 生成报告。

预期效果：

1. 生成策略返回策略类型、参数、代码、rationale。
2. 调参返回 best_trial + top_trials。
3. 报告 markdown 包含建议，并可附 citation。

实现原理：

1. generate: LLM 优先；若配置允许且 LLM 不可用，则走确定性 fallback。
2. tune: 参数网格笛卡尔展开后逐个回测并按目标排序。
3. report: 组合量化规则建议 + 可选 LLM 文本 + KB 引证。

## 4.11 Chat 会话辅助

操作路径：同页「会话助手」。

步骤：

1. 输入策略意图（如“请生成 RSI 策略”）。
2. 发送消息。

预期效果：

1. 生成 user/assistant 双消息。
2. 对策略类意图，后端可能自动新建策略并在返回中提示。

实现原理：

1. chat 后端有“策略意图识别”关键字规则。
2. 命中后调用策略生成逻辑并落库。

---

## 5. 引导式功能验收清单（可直接执行）

说明：

1. `P0` = 必须通过（核心可用性）。
2. `P1` = 重要增强项（建议通过）。
3. `P2` = 进阶与边界项。

| 优先级 | 用例ID | 验收目标 | 操作步骤（简版） | 预期结果（通过标准） |
| --- | --- | --- | --- | --- |
| P0 | ENV-001 | 一键启动可用 | 运行 `start-all.cmd`（`start-all.bat` 兼容） | Backend/Frontend 双窗口启动成功，`.runtime/backend-port.txt` 存在 |
| P0 | ENV-002 | API 文档可访问 | 打开 `/docs` | 页面可打开，无 5xx |
| P0 | PF-001 | 组合创建 | 新建组合，资金 100000 | 返回成功并跳详情页；现金与总值=100000 |
| P0 | PF-002 | 组合编辑 | 编辑名称、状态 | 保存成功；列表筛选可按 active/inactive 生效 |
| P0 | PF-003 | 组合删除 | 删除组合并确认 | 列表消失；再访问详情返回 404 |
| P0 | TRD-001 | BUY 成功路径 | 买入 AAPL 10 股 | 交易记录新增；现金按金额+手续费减少 |
| P0 | TRD-002 | SELL 成功路径 | 卖出 AAPL 5 股 | 交易记录新增；realized_pnl 合理变化 |
| P0 | TRD-003 | 卖出数量校验 | 卖出超过持仓数量 | 返回 400，提示 Insufficient holding quantity |
| P0 | TRD-004 | 买入代码校验 | 用明显非法代码 BUY | 返回 400，提示 Invalid/unsupported symbol |
| P0 | QTE-001 | 报价刷新 | 点击“刷新报价” | 价格更新或出现降级提示但页面不中断 |
| P0 | ANA-001 | 分析页汇总 | 打开分析页并选组合 | summary/allocation/trend/monthly 数据可展示 |
| P0 | ANA-002 | CSV 导出 | 分别导出 3 类 CSV | 文件下载成功；字段与页面一致 |
| P0 | STR-001 | 策略创建 | 新建 MA/RSI/momentum 任一策略 | 创建成功，策略列表可见 |
| P0 | BT-001 | 回测执行 | 选择策略执行回测 | 状态 completed，关键指标非空 |
| P0 | BT-002 | 回测非法日期校验 | start_date > end_date | 返回 400，明确日期错误 |
| P0 | KB-001 | 文本入库 | 在知识库保存一段文本 | 返回 chunk_count > 0 |
| P0 | KB-002 | 检索命中 | 用关键词搜索 | 命中 hits，含 score/reference_id |
| P0 | AG-001 | Agent 健康检查 | 调 `GET /api/v1/agent/health` | 返回 200 或 503（与 llm_required/configured 一致） |
| P0 | AG-002 | Agent 生成策略 | 提示词生成策略 | 返回 detected_strategy_type + parameters + code |
| P0 | AG-003 | Agent 自动调参 | 执行 tune | 返回 best_trial 与 top_trials |
| P0 | AG-004 | Agent 复盘报告 | 用 backtest_id 生成 report | 返回 markdown，含建议段落 |
| P1 | VER-001 | 版本快照 | 创建策略快照 | version 列表数量增加 |
| P1 | VER-002 | 版本对比 | 选择>=2版本对比 | 返回每版本回测汇总指标 |
| P1 | MD-001 | 市场数据入库 | 手动 ingest 指定 symbol | results 显示 completed 且 ingested>=1 |
| P1 | MD-002 | 健康检查细节 | 查询 status | 返回 total_bars、gap_estimate、last_ingest |
| P1 | CHAT-001 | Chat 会话 | 发送策略类消息 | 会话消息新增，必要时策略自动落库 |
| P1 | TEL-001 | 前端埋点 | 页面跳转与点击 | 后端日志出现 `[NAV]` / `[CLICK]` 行 |
| P2 | KB-003 | 治理严格模式 | 检索 policy=`strict` | 每文档命中数受限，fallback 行为收敛 |
| P2 | KB-004 | 检索过滤器 | 设置 `allowed_source_types` 等 | 命中仅保留符合条件的文档 |
| P2 | AG-005 | 引证过滤 | report 指定 allowed_source_types=pdf | 若无 PDF 证据，citations 可为空（非报错） |
| P2 | NFR-001 | 中间件健壮性 | 压测或异常日志场景 | 请求日志异常不应导致 API 失败 |

### 5.1 建议验收顺序（严格执行版）

1. 先跑 `ENV/PF/TRD/ANA`（业务核心）。
2. 再跑 `STR/BT/VER`（策略链路）。
3. 再跑 `MD/KB/AG/CHAT`（AI 与数据链路）。
4. 最后跑 `P2` 边界项。

### 5.2 缺陷分级建议

1. P0 失败 -> 直接判定 `No-Go`。
2. P1 失败 -> 需有 workaround 才可 `Conditional Go`。
3. P2 失败 -> 可记录为迭代缺陷，但不阻塞核心验收。

---

## 6. 功能实现原理（通俗但足够深入）

## 6.1 组合与交易为什么“数值看起来合理”

1. 组合总值是实时汇总值，不是静态字段: `current_value = cash_balance + sum(holding.market_value)`。
2. 买入用加权平均成本更新持仓均价。
3. 卖出时计算已实现盈亏，不会重写历史买入成本。

## 6.2 回测结果怎么来的

1. 回测从本地 bars 数据读取价格序列。
2. 信号引擎按策略类型（MA/RSI/Momentum/Custom）生成 BUY/SELL/HOLD。
3. 按 `allocation_per_trade` 与 `commission_rate` 执行交易模拟。
4. 结束时强制平仓，保证收益/回撤/胜率口径稳定。

## 6.3 报价为什么有时“慢但不断”

1. provider 会按 symbol 类型走优先链路（CN 优先 akshare，US 优先 yfinance/stooq）。
2. 内存缓存减少频繁外部请求。
3. 外部请求失败时优先回退最近缓存，保证页面可用性。

## 6.4 市场数据为何强调“先入库再回测”

1. 回测不直接连外网抓数据，而是查本地表。
2. `ingest` 负责把外部历史 bars 标准化并 upsert 到本地。
3. `status/gap_estimate` 帮你判断数据完整性，避免“无效回测”。

## 6.5 知识库检索为何有 governance flags

1. 检索分数来自多信号融合（vector + fts + term overlap + freshness）。
2. governance 会限制“同一文档过度占位”与“低分证据滥入”。
3. 可通过 policy（strict/balanced/recall）调节精确率与召回率。

## 6.6 Agent 为什么有“可用/不可用”两种启动行为

1. `AGENT_REQUIRE_LLM=true` 且未配置 key 时，后端会 fail-fast。
2. `AGENT_REQUIRE_LLM=false` 时，部分能力允许 deterministic fallback。
3. `/agent/health` 是验收前必须看的状态面板。

---

## 7. 已知问题与验收口径

| 编号 | 现象 | 影响 | 建议口径 |
| --- | --- | --- | --- |
| KN-001 | 前端多处中文文案出现乱码（如导航、按钮文案） | 可用性与可读性受影响 | 若以中文用户为主，建议按 P1 缺陷处理；不影响后端业务计算正确性 |
| KN-002 | LLM 未配置时，Agent 严格模式返回 503 或启动失败 | AI链路不可用 | 验收前先确认 `agent/health` 与环境变量策略 |
| KN-003 | 未先入库行情就回测会失败（No local bars） | 回测链路阻断 | 将“市场数据入库”纳入回测前置步骤 |
| KN-004 | 后端端口可能不是固定 8001（脚本会找可用端口） | 前后端联调易混淆 | 一律以 `.runtime/backend-port.txt` 为准 |

---

## 8. 验收记录模板（直接复制使用）

```markdown
# StockTracker UAT 执行记录

- 测试日期:
- 测试环境:
- 后端地址:
- 前端地址:
- 测试人:

## 用例执行结果

| 用例ID | 结果(PASS/FAIL/BLOCKED) | 证据(截图/日志/接口响应) | 备注 |
| --- | --- | --- | --- |
| ENV-001 |  |  |  |
| PF-001 |  |  |  |
| TRD-001 |  |  |  |
| ANA-001 |  |  |  |
| STR-001 |  |  |  |
| BT-001 |  |  |  |
| KB-001 |  |  |  |
| AG-001 |  |  |  |

## 缺陷列表

| Defect ID | 严重级别(P0/P1/P2) | 现象 | 复现步骤 | 当前状态 |
| --- | --- | --- | --- | --- |
| BUG-001 |  |  |  |  |

## 最终结论

- Go / No-Go:
- 阻塞项:
- 后续动作:
```

---

## 9. 一句话总结

这套系统已经具备“组合管理 -> 数据入库 -> 策略回测 -> 版本管理 -> 知识库检索 -> Agent 调参与报告”的完整闭环，按照本手册执行即可完成结构化、可复现、可追责的项目验收。
