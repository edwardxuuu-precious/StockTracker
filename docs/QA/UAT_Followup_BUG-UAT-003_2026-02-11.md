# BUG-UAT-003 Follow-up Plan

## 基本信息

- Defect ID: BUG-UAT-003
- 来源: UAT（2026-02-11）
- 当前状态: Fixed (Mitigated, Monitoring)
- 优先级: High
- 放行影响: 不阻塞本次放行，但影响 Agent 报告体验与稳定性

## 问题描述

调用 `POST /api/v1/agent/backtests/{backtest_id}/report` 时，出现 LLM 请求超时，返回错误：

`LLM is required for AI backtest insights: Request timed out.`

## 目标

1. 降低超时失败率，提升报告接口成功率。
2. 在 LLM 不可用时保证可降级返回，避免用户完全失败。
3. 提供可观测性数据，支持后续容量与供应商策略决策。

## 执行项

1. 超时与重试
- 将 LLM 请求超时调高到 `90-120s`（配置化）。
- 增加最多 `3` 次重试，采用指数退避。
- 区分可重试错误（超时、临时网络错误）与不可重试错误（参数错误、鉴权错误）。

2. 降级策略（Fallback）
- 当 LLM 连续失败时，返回 deterministic 报告（基于已有回测指标模板生成）。
- 响应中增加字段标记：`fallback_used=true`、`fallback_reason`。

3. 可观测性
- 增加日志字段：provider、latency_ms、retry_count、timeout、error_type。
- 增加监控指标：成功率、P95 时延、fallback 比例、超时率。

4. 回归测试
- 增加集成测试：正常路径、超时重试成功、超时后 fallback 成功。
- 校验响应结构稳定，确保前端可兼容展示 fallback 场景。

## 验收标准

1. 报告接口在测试环境连续 100 次调用，成功率达到 `>= 95%`（含 fallback 成功）。
2. LLM 不可用时，接口仍返回可阅读报告，不再直接失败。
3. 日志与监控可追踪每次调用的超时、重试、fallback 细节。

## 建议排期

1. D1: 完成超时/重试与配置项。
2. D2: 完成 fallback 与接口字段扩展。
3. D3: 完成测试、监控接入与联调验收。

## 执行落地结果（2026-02-11）

1. D1 已完成（超时与重试）
- 已新增配置项：`AGENT_LLM_TIMEOUT_SECONDS`、`AGENT_LLM_MAX_RETRIES`、`AGENT_LLM_RETRY_BASE_SECONDS`、`AGENT_LLM_RETRY_MAX_SECONDS`。
- 已实现可重试错误判定与指数退避重试。

2. D2 已完成（Fallback）
- `POST /api/v1/agent/backtests/{backtest_id}/report` 在 LLM 不可用时不再返回 503。
- 接口将返回 deterministic fallback 报告，并包含 `fallback_used=true` 与 `fallback_reason`。

3. D3 已完成（可观测性与测试）
- 已新增结构化日志字段：`provider`、`latency_ms`、`retry_count`、`timeout`、`error_type`、`fallback_used`。
- 已新增指标端点：`GET /api/v1/telemetry/agent-report-metrics?window=200`。
- 指标包含：`success_rate`、`p95_latency_ms`、`fallback_ratio`、`timeout_rate`、`llm_p95_latency_ms`。

## 100 次稳定性验证记录（2026-02-11）

- 环境：`TestClient + 临时 SQLite`（可复现脚本）
- 负载：连续 100 次调用 `POST /api/v1/agent/backtests/{id}/report`
- 注入策略：每 10 次模拟 1 次 LLM timeout（用于验证 fallback 路径）

验证结果：
- `total_calls`: 100
- `http_200`: 100
- `success_rate`: 1.0
- `fallback_count`: 10
- `fallback_ratio`: 0.1
- `timeout_rate`: 0.1
- `p95_latency_ms`: 3.1872
- `llm_p95_latency_ms`: 1200.0

结论：
- 满足验收标准 1（成功率 >= 95%，含 fallback）。
- 满足验收标准 2（LLM 不可用仍返回可读报告）。
- 满足验收标准 3（日志与指标可追踪 timeout/retry/fallback）。

## 关联文档

- `docs/QA/UAT_Execution_Log_2026-02-11.md`
- `docs/QA/UAT_Defects_2026-02-11.md`
- `docs/QA/UAT_Final_Decision_2026-02-11.md`
