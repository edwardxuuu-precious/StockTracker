# StockTracker 交接文档（给 Claude Code）

Last updated: `2026-02-10`

## 1) 项目总目标

构建一个本地优先的量化研究系统（当前聚焦股票），满足：

1. 本地市场数据入库与更新（US + CN）
2. 使用本地数据进行回测（非模拟）
3. Agent 自然语言交互：策略生成、参数调优、报告生成
4. 知识库支持 `pdf/txt/json` 入库与检索引用
5. 策略版本管理、结果对比与复盘闭环

当前不做：

1. 云部署
2. 对外商用合规落地
3. 新资产类别（基金/期货）正式扩展

## 2) 事实来源（按优先级）

Claude 接管时请优先读取并以此为准：

1. `docs/QA/UAT_RealUsage_Log_2026-02.md`（最新真实使用记录，最高优先级）
2. `docs/QA/UAT_FullChain_Execution_2026-02-09.md`（全链路 UAT 基线）
3. `docs/Progress/Master_Progress.md`（里程碑历史）

说明：`Master_Progress` 最近更新时间是 `2026-02-09`，Day3 结果请以 `UAT_RealUsage_Log_2026-02.md` 为准。

## 3) 当前进度（截至 2026-02-10）

### 3.1 系统建设状态

1. 全链路 UAT：`34 PASS / 0 FAIL / 0 BLOCKED`
2. Real Usage Day1：`4/4 PASS`
3. Real Usage Day2：`4/4 PASS`
4. Real Usage Day3：`4/4 PASS`

### 3.2 Day3 关键结论

1. 宽窗口数据更新完成：
   - US: `AAPL/MSFT/NVDA`，`1d`，新增约 `90` bars/标的
   - CN: `600519/000001`，`1d`，新增约 `87` bars/标的
2. 保守策略变体已创建：`strategy_id=18`
3. 基线 vs 变体对比（`backtest 31 -> 32`）：
   - `delta_return=+2.1371`
   - `delta_sharpe=+0.3942`
   - `delta_drawdown=-3.0572`（回撤改善）
   - `delta_trade_count=-10`
4. Agent 报告链路正常：`quantitative=2`，`qualitative=2`，`citations=5`
5. 风险：绝对收益与 Sharpe 仍为负，需要持续真实使用验证。

## 4) 运行与记录约束（必须遵守）

1. 不引入 `progress-tracker MCP`（当前维护中，暂不使用）
2. 每次动作必须写 operation log：输入、输出、耗时、异常、证据路径
3. 证据统一落到 `.runtime/real_usage/<timestamp>/`
4. 月度真实使用日志只更新：`docs/QA/UAT_RealUsage_Log_2026-02.md`
5. 遇到异常先记录证据，再决定是否记为缺陷

## 5) 下一步任务清单（Day4）

目标：继续“用户视角真实使用”，验证策略在更长周期是否可转正，暂不扩新功能。

### RU-D4-01 数据扩样本

1. 扩展时间窗（建议覆盖更长周期）
2. 增加符号数（US + CN）
3. 完成入库并校验 `completed/partial/failed` 与 ingestion 记录

验收标准：

1. 两个市场都至少有可用新增数据
2. 无系统级崩溃，状态可追踪

### RU-D4-02 回测对比

1. 在同一窗口、同一 symbols 上运行 baseline 与 conservative variant
2. 对比 `total_return/sharpe/max_drawdown/win_rate/trade_count`

验收标准：

1. 两次回测均 `status=completed`
2. 指标差异可解释，且有证据文件

### RU-D4-03 Agent 报告核验

1. 对当轮重点回测生成报告
2. 校验定量、定性建议与 citations 数量

验收标准：

1. 接口 `200`
2. `quantitative_recommendations`、`qualitative_recommendations`、`citations` 均非空

### RU-D4-04 复盘结论

1. 输出有效参数、失效条件、下一轮动作
2. 给出“是否进入长期实盘研究阶段”的判断（条件化结论）

验收标准：

1. 复盘结论可执行
2. 与当轮证据一致

## 6) Claude 接管执行模板（可直接粘贴）

```text
请接管 StockTracker 项目，先完成三件事：
1) 复述你理解的总目标
2) 复述你确认的当前进度（以 docs/QA/UAT_RealUsage_Log_2026-02.md 为准）
3) 给出 Day4 执行顺序（RU-D4-01..04）

执行约束：
- 不做云部署，不扩新功能，先做真实使用验证
- 每一步都写操作日志与证据路径
- 证据写入 .runtime/real_usage/<timestamp>/
- 更新 docs/QA/UAT_RealUsage_Log_2026-02.md

完成后输出：
- Day4 每项 PASS/FAIL
- 关键指标变化
- 风险与下一步建议
```

## 7) 快速核验命令

1. 后端可用性：读取 `.runtime/backend-port.txt` 后访问 `/` 与 `/docs`
2. 回归测试（可选）：`python -m pytest backend/tests -q`
3. 当前真实使用主日志：`docs/QA/UAT_RealUsage_Log_2026-02.md`

