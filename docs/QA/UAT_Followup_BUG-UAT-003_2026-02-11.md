# BUG-UAT-003 Follow-up Plan

## 基本信息

- Defect ID: BUG-UAT-003
- 来源: UAT（2026-02-11）
- 当前状态: Open (Non-blocking)
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

## 关联文档

- `docs/QA/UAT_Execution_Log_2026-02-11.md`
- `docs/QA/UAT_Defects_2026-02-11.md`
- `docs/QA/UAT_Final_Decision_2026-02-11.md`
