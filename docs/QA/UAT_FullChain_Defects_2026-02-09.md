# StockTracker 全链路 UAT 缺陷清单（Run 1）

Run ID: `20260209_195743`  
Generated: `2026-02-09`

## Defect List

| Defect ID | Severity | Case ID | Summary | Impact | Status | Evidence |
| --- | --- | --- | --- | --- | --- | --- |
| `UAT-BUG-001` | `P1` | `UAT-D-002` | 回测详情中 `final_value` 与 `equity_curve` 末值不一致。 | 回测结果一致性破坏，影响复盘可信度。 | `Closed (Retest Pass)` | `.runtime/uat/20260209_195743/UAT-D-002_result.json` |
| `UAT-BUG-002` | `P0` | `UAT-E-003` | `POST /api/v1/agent/backtests/{id}/report` 返回 `500`。 | Agent 报告主流程不可用。 | `Closed (Fix + Retest Pass)` | `.runtime/uat/20260209_195743/UAT-E-003_result.json`, `backend/app/main.py` |
| `UAT-BUG-003` | `P1` | `UAT-F-001` | JSON 文档入库 `chunk_count=0`（txt/pdf 正常）。 | 知识库 JSON 资料无法有效检索与引用。 | `Closed (Retest Pass)` | `.runtime/uat/20260209_195743/UAT-F-001_result.json` |
| `UAT-BUG-004` | `P1` | `UAT-F-003` | 检索治理不符合预期：`allowed_source_types` 过滤未生效；`allow_fallback=false` 时仍返回低分命中。 | 治理策略失真，影响检索可控性。 | `Closed (Retest Pass)` | `.runtime/uat/20260209_195743/UAT-F-003_result.json`, `.runtime/uat/20260209_195743/UAT_retest_P1.json` |
| `UAT-BUG-005` | `P0` | `UAT-F-004` | Agent 报告引用治理场景下接口持续 `500`。 | Agent+KB 联动不可用，阻塞核心用户路径。 | `Closed (Fix + Retest Pass)` | `.runtime/uat/20260209_195743/UAT-F-004_result.json`, `backend/app/main.py` |

## Notes

- `UAT-BUG-002` 与 `UAT-BUG-005` 指向同一类高优先故障（报告接口 500），已通过日志稳健性修复与复测关闭。
