# 给 Codex 的 UAT P0 修复任务交接提示词

**使用说明**: 将以下提示词直接复制粘贴给 Codex，启动新的对话会话。

---

## 📋 完整交接提示词

```
你好 Codex！我需要你接手 StockTracker 项目的 UAT（用户验收测试）后续工作。

**项目背景**:
- 项目路径: c:\Users\edwar\Desktop\StockTracker-main
- 当前分支: main
- 最新提交: 2f3c46b (docs(qa): add real-user manual and archive legacy QA docs)

**已完成工作**:
我的前任（Claude Sonnet 4.5）已经成功修复了初次 UAT 中发现的 2 个 P0 阻塞缺陷：
1. ✅ BUG-UAT-001: CSV 导出功能未区分 report_type
2. ✅ BUG-UAT-002: 知识库检索返回空结果

两个缺陷都已通过复测验证，修复代码已经应用到代码库中。

**关键修改文件**:
- backend/app/api/v1/analytics.py (第 280 行) - 添加了 Query alias
- backend/app/config.py (第 47, 49 行) - 添加了 "text" 到 allowed source types

**你的任务**:
请阅读详细的交接文档 `docs/QA/UAT_P0_Fixes_Handoff_2026-02-11.md`，然后按照其中第 4 节"优先级 TODO 清单"完成以下工作：

### 🔴 P0 - 必须立即完成
1. 清理临时 debug 代码
   - 移除 `backend/app/api/v1/knowledge_base.py` 第 122 和 151 行的 print() 语句
   - 这些是调试时添加的，不应出现在生产代码中

2. 更新验收文档
   - 在 `docs/QA/UAT_Defects_2026-02-11.md` 中，将 BUG-UAT-001 和 BUG-UAT-002 的状态从 "Open" 更新为 "Fixed → Closed"
   - 在 `docs/QA/UAT_Execution_Log_2026-02-11.md` 末尾添加"Retest 章节"，记录复测结果（可参考交接文档第 2 节）
   - 创建新文件 `docs/QA/UAT_Final_Decision_2026-02-11.md`，使用交接文档第 8.1 节的模板，填写放行决策

3. 提交代码到 Git
   - 使用交接文档第 3.4 节提供的 commit message 模板
   - 确保只提交实际修复代码，不提交临时调试脚本

### 🟡 P1 - 建议在今天完成
4. 执行完整的 P0 用例回归测试
   - 重新运行 UAT 主手册中的所有 P0 用例（ENV-001 ~ AG-003）
   - 确保修复没有引入新的回归问题
   - 记录任何新发现的问题

5. 实施 BUG-UAT-003 的短期修复（LLM 超时问题）
   - 这个不阻塞放行，但建议尽快解决
   - 具体方案见交接文档第 4 节 P1 第一项

### 🟢 P2 及以下 - 可选
- 根据时间和优先级选择性执行

**重要提醒**:
1. 在开始工作前，请先阅读 `docs/QA/UAT_P0_Fixes_Handoff_2026-02-11.md` 第 2 节，了解每个缺陷的完整修复过程和根本原因
2. 如果遇到问题，参考交接文档第 7.4 节"常见问题排查"
3. 所有文档更新请保持与现有格式一致，参考已有的 UAT 文档风格

**验证方法**:
在提交代码前，请运行以下快速验证命令（见交接文档第 7.2 节）:
```bash
# 验证 BUG-UAT-001 修复
curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=summary" | head -1
curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=holdings" | head -1

# 验证 BUG-UAT-002 修复
curl -X POST http://localhost:8001/api/v1/kb/search -H "Content-Type: application/json" -d '{"query":"moving average","mode":"fts"}'
```

期望结果：CSV 导出三种格式不同，KB 检索返回非空 hits。

**环境状态**:
- Backend 正在 http://localhost:8001 运行（task ID: b43474f）
- 数据库 backend/stocktracker.db 包含测试数据
- 所有依赖已安装，venv 已激活

请确认你已阅读交接文档，然后开始执行 P0 任务。如有疑问，请随时询问！
```

---

## 🎯 简化版提示词（如果 Codex 需要更简洁的指令）

```
你好！接手 StockTracker UAT 验收任务。

**已完成**: 2 个 P0 缺陷已修复并通过测试
**你的任务**:
1. 读取 `docs/QA/UAT_P0_Fixes_Handoff_2026-02-11.md`
2. 按第 4 节 TODO 清单执行：
   - P0: 清理 debug 代码 + 更新文档 + 提交 Git
   - P1: 回归测试 + LLM 超时修复

**关键文件**:
- 修复代码: backend/app/api/v1/analytics.py, backend/app/config.py
- 交接文档: docs/QA/UAT_P0_Fixes_Handoff_2026-02-11.md
- 待更新: docs/QA/UAT_Defects_2026-02-11.md, UAT_Execution_Log_2026-02-11.md

开始前先读交接文档确认细节。准备好了吗？
```

---

## 📝 补充说明

### 为什么需要交接？
前任 Claude 会话的 context 即将用尽，需要将任务移交给新的 Codex 会话。交接文档确保：
1. ✅ 所有修复细节完整记录
2. ✅ 根本原因分析清晰可追溯
3. ✅ 后续任务优先级明确
4. ✅ 验证方法和排查指南完备

### 交接检查清单
在移交前，确认：
- [x] ✅ 交接文档已创建并包含所有关键信息
- [x] ✅ 代码修改已应用但尚未提交 Git
- [x] ✅ 临时调试文件已标记但未删除
- [x] ✅ Backend 服务仍在运行
- [x] ✅ 复测验证已通过

### 建议的工作流
1. Codex 读取交接文档
2. Codex 执行 P0 任务（清理 + 文档 + 提交）
3. Codex 执行 P1 回归测试
4. Codex 报告完成状态
5. 用户进行最终人工验收和签署

### 如果 Codex 遇到困难
可以提供额外的上下文文件：
- `docs/QA/Real_User_Manual_and_Acceptance_Checklist.md` - 完整验收标准
- `docs/QA/UAT_Execution_Log_2026-02-11.md` - 初次执行日志
- `docs/QA/UAT_Retest_Plan_2026-02-11.md` - 复测计划

---

**使用方法**: 复制上方"完整交接提示词"或"简化版提示词"，粘贴到新的 Codex 对话窗口即可。
