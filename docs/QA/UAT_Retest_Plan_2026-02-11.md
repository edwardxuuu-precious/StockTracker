# StockTracker UAT 复测计划

**生成日期**: 2026-02-11
**关联验收日志**: docs/QA/UAT_Execution_Log_2026-02-11.md
**关联缺陷台账**: docs/QA/UAT_Defects_2026-02-11.md

---

## 1. 复测范围概述

本复测计划针对初次 UAT 中标记为 **FAIL** 或 **BLOCKED** 的用例，以及需要补充验证的 **PARTIAL** 和 **SKIP** 用例。

### 1.1 需要复测的用例汇总

| 用例ID | 优先级 | 初次状态 | 阻塞原因/缺陷ID | 复测优先级 |
|--------|--------|---------|----------------|-----------|
| ANA-002 | P0 | FAIL | BUG-UAT-001 | 🔴 P0 (阻塞放行) |
| KB-002 | P0 | FAIL | BUG-UAT-002 | 🔴 P0 (阻塞放行) |
| AG-004 | P0 | BLOCKED | BUG-UAT-003 | 🟡 P1 (外部依赖) |
| ENV-001 | P0 | PARTIAL | 一键启动未验证 | 🟡 P1 |
| MD-002 | P1 | PARTIAL | 查询逻辑未深入验证 | 🟢 P2 |
| CHAT-001 | P1 | SKIP | 时间限制 | 🟢 P2 |
| TEL-001 | P1 | SKIP | 时间限制 | 🟢 P2 |
| KB-003 ~ KB-004 | P2 | SKIP | 时间限制 | 🔵 P3 |
| AG-005 | P2 | SKIP | 时间限制 | 🔵 P3 |
| NFR-001 | P2 | SKIP | 时间限制 | 🔵 P3 |

---

## 2. P0 阻塞项复测 (必须通过才能放行)

### 2.1 ANA-002: CSV 导出功能复测

#### 前置条件
- ✅ BUG-UAT-001 已修复（CSV 导出端点实现 report_type 区分逻辑）
- ✅ 后端服务已重启并加载新代码
- ✅ 至少存在一个组合，包含持仓和交易记录

#### 复测步骤
1. **准备测试数据**:
   ```bash
   # 创建测试组合
   curl -X POST http://localhost:8001/api/v1/portfolios/ \
     -H "Content-Type: application/json" \
     -d '{"name":"Retest_Portfolio","initial_capital":100000}'

   # 执行 2 笔交易（1 BUY + 1 SELL）
   curl -X POST http://localhost:8001/api/v1/portfolios/1/trades \
     -H "Content-Type: application/json" \
     -d '{"action":"BUY","symbol":"AAPL","quantity":10,"price":150,"commission":1}'

   curl -X POST http://localhost:8001/api/v1/portfolios/1/trades \
     -H "Content-Type: application/json" \
     -d '{"action":"SELL","symbol":"AAPL","quantity":5,"price":160,"commission":1}'
   ```

2. **导出三种 CSV**:
   ```bash
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=summary" -o summary.csv
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=holdings" -o holdings.csv
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=trades" -o trades.csv
   ```

3. **验证 CSV 内容**:
   ```bash
   # 验证 summary.csv
   head -2 summary.csv
   # 期望 header: portfolio_id,portfolio_name,initial_capital,cash_balance,...
   # 期望 1 行数据

   # 验证 holdings.csv
   head -2 holdings.csv
   # 期望 header: portfolio_id,symbol,quantity,average_cost,current_price,market_value,unrealized_pnl,...
   # 期望 N 行数据（N = 当前持仓数量）

   # 验证 trades.csv
   head -5 trades.csv
   # 期望 header: trade_id,portfolio_id,symbol,action,quantity,price,commission,amount,realized_pnl,trade_time,...
   # 期望 M 行数据（M = 历史交易总数）
   ```

#### 通过标准
- ✅ 三个 CSV 文件的 header 和内容**不同**
- ✅ `summary.csv` 包含 1 行汇总数据，字段匹配组合级别指标
- ✅ `holdings.csv` 包含当前持仓明细，至少有 symbol/quantity/average_cost 字段
- ✅ `trades.csv` 包含历史交易记录，至少有 trade_id/action/symbol/price/trade_time 字段
- ✅ 字段值与 API 返回的 JSON 数据一致（抽查 2-3 个字段）

#### 失败时行动
- 记录具体失败现象（哪个 report_type 仍然错误）
- 将缺陷重新提交给开发团队
- **不可放行生产**

---

### 2.2 KB-002: 知识库检索功能复测

#### 前置条件
- ✅ BUG-UAT-002 已修复（KB search 逻辑或索引问题已解决）
- ✅ 后端服务已重启
- ✅ 数据库 FTS 索引已验证正常

#### 复测步骤
1. **清空旧测试数据**（可选，避免干扰）:
   ```bash
   # 删除旧文档（如果提供 DELETE 接口）
   # 或直接清空数据库 documents/chunks 表
   ```

2. **入库新测试文档**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/kb/ingest-text \
     -F 'content=The moving average crossover strategy is a popular technical analysis method. It uses two moving averages with different periods to generate buy and sell signals. When the short-term MA crosses above the long-term MA, it produces a bullish signal.' \
     -F 'title=MA_Strategy_Guide' \
     -F 'source_type=text' \
     -F 'source_name=ma_guide.txt'
   ```
   期望返回: `chunk_count > 0`

3. **执行多种模式检索**:
   ```bash
   # 测试 1: FTS 模式 + 精确关键词
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"moving average","mode":"fts","max_results":10}' | jq .

   # 测试 2: Hybrid 模式 + 语义查询
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"technical analysis crossover","mode":"hybrid","max_results":5}' | jq .

   # 测试 3: 宽松治理策略
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"bullish signal","mode":"fts","governance_policy":"recall"}' | jq .
   ```

4. **验证返回结果**:
   - 检查 `hits` 数组是否非空
   - 检查每个 hit 是否包含: `chunk_id`, `document_id`, `content`, `score`, `reference_id`
   - 验证 `content` 字段是否包含查询词或相关内容

#### 通过标准
- ✅ 至少一个查询返回 `hits.length > 0`
- ✅ 返回的 chunk 内容与查询词语义相关
- ✅ `score` 分数合理（通常 > 0.5 表示中等相关性）
- ✅ `reference_id` 和 `source_name` 可追溯到原始文档

#### 失败时行动
- 记录失败的查询词和模式
- 检查数据库中 chunks 表和 chunks_fts 表是否有数据
- 将详细日志提交给开发团队
- **不可放行生产**

---

## 3. P1 高优先级复测 (建议通过)

### 3.1 AG-004: Agent 报告生成复测

#### 前置条件
- ⚠️ BUG-UAT-003 的**短期修复**已实施（增加 timeout、retry、fallback）
- ✅ 至少存在一个已完成的 backtest（如 backtest_id=2）
- ⚠️ LLM API 网络条件改善（或后端已实现 fallback）

#### 复测步骤
1. **验证 LLM 健康状态**:
   ```bash
   curl http://localhost:8001/api/v1/agent/health | jq .
   ```
   期望: `ok=true`, `configured=true`, `reachable=true` (如果增加了 reachability check)

2. **调用报告生成（不包含 KB）**:
   ```bash
   curl -X POST http://localhost:8001/api/v1/agent/backtests/2/report \
     -H "Content-Type: application/json" \
     -d '{"include_kb_citations":false}' \
     --max-time 120 | jq .
   ```

3. **如果超时，验证 fallback**:
   - 检查返回是否包含基于规则的量化建议（非 LLM 生成）
   - 确认不返回 500 错误

4. **如果成功，验证报告内容**:
   ```bash
   # 检查返回的 markdown 字段
   # 期望包含: 指标解读、优化建议等段落
   ```

#### 通过标准
- ✅ **理想**: LLM 调用成功，返回完整 markdown 报告
- ⚠️ **可接受**: LLM 超时但返回 fallback 报告（基于量化规则）
- ❌ **不可接受**: 返回 500 错误或无任何响应

#### 失败时行动
- 如果仍然超时且无 fallback: 标记为"已知限制"，在发布说明中告知用户
- 不阻塞放行，但需在文档中明确说明依赖外部 LLM 服务

---

### 3.2 ENV-001: 一键启动脚本复测

#### 前置条件
- ✅ 后端和前端服务已停止
- ✅ `.runtime` 目录可写

#### 复测步骤
1. **确保服务已停止**:
   ```bash
   # 停止之前的后台任务
   # 或直接重启系统
   ```

2. **执行一键启动脚本**:
   ```bash
   # Windows
   start-all.bat

   # 或通过命令行观察输出（非后台）
   cmd /c start-all.bat
   ```

3. **验证启动状态**:
   - 检查是否自动打开两个终端窗口（Backend / Frontend）
   - 等待 10-15 秒后检查:
     ```bash
     # 验证端口文件
     cat .runtime/backend-port.txt

     # 验证后端健康
     curl http://localhost:$(cat .runtime/backend-port.txt)/api/v1/portfolios/

     # 验证前端可访问（浏览器或 curl）
     curl -I http://localhost:5173
     ```

#### 通过标准
- ✅ Backend 和 Frontend 窗口自动启动
- ✅ `.runtime/backend-port.txt` 文件存在且包含有效端口号
- ✅ Backend API 可访问（返回 200）
- ✅ Frontend 页面可访问（返回 200 HTML）

#### 失败时行动
- 记录具体失败步骤（哪个服务未启动）
- 检查脚本日志和错误输出
- 如果仅脚本问题但手动启动可用: 标记为"文档问题"，更新 Runbook

---

## 4. P2 补充验证复测 (可选)

### 4.1 MD-002: 市场数据健康检查

#### 复测步骤
```bash
# 先确保有数据
curl -X POST http://localhost:8001/api/v1/market-data/ingest \
  -H "Content-Type: application/json" \
  -d '{"symbols":["AAPL"],"market":"US","interval":"1d","start":"2025-01-01","end":"2025-12-31"}'

# 查询健康状态
curl "http://localhost:8001/api/v1/market-data/status?symbol=AAPL" | jq .
```

#### 通过标准
- ✅ 返回 `total_bars`, `gap_estimate`, `last_ingest` 等字段
- ✅ `total_bars` 与实际入库数据一致

---

### 4.2 CHAT-001: Chat 会话功能

#### 复测步骤
```bash
# 创建会话并发送策略类消息
curl -X POST http://localhost:8001/api/v1/chat/messages \
  -H "Content-Type: application/json" \
  -d '{"session_id":"test_session","role":"user","content":"请生成一个 RSI 策略，周期设为 14"}' | jq .

# 检查是否自动创建策略
curl http://localhost:8001/api/v1/strategies/ | jq .
```

#### 通过标准
- ✅ 返回 user 和 assistant 消息
- ✅ 如果命中策略意图，策略列表中出现新策略

---

### 4.3 TEL-001: 前端埋点验证

#### 复测步骤
```bash
# 查看后端日志
tail -50 .runtime/backend.log | grep -E '\[NAV\]|\[CLICK\]'
```

#### 通过标准
- ✅ 日志中出现导航和点击事件记录

---

### 4.4 P2 边界用例 (KB-003, KB-004, AG-005, NFR-001)

这些用例为高级功能和边界场景，可根据时间和优先级选择性执行。具体步骤参考主手册第 5 章对应用例说明。

---

## 5. 复测执行顺序（强制）

1. **第一优先级** (阻塞放行): ANA-002, KB-002
2. **第二优先级** (重要但不阻塞): AG-004, ENV-001
3. **第三优先级** (补充验证): MD-002, CHAT-001, TEL-001
4. **第四优先级** (可选): P2 边界用例

---

## 6. 复测通过标准（整体）

### 6.1 最低放行标准
- ✅ ANA-002 **必须** PASS
- ✅ KB-002 **必须** PASS
- ⚠️ AG-004 至少有 fallback 机制（不返回 500）
- ⚠️ ENV-001 至少手动启动可用（一键脚本可标记为"已知问题"）

### 6.2 理想放行标准
- ✅ 所有 P0 和 P1 用例 100% PASS
- ✅ P2 用例至少 50% 覆盖

---

## 7. 复测失败应急预案

### 7.1 如果 P0 阻塞项仍未通过
- **立即暂停放行流程**
- 召集开发团队紧急修复
- 重新提交 hotfix 并再次执行本复测计划

### 7.2 如果 P1 项仍有问题
- 评估影响范围和绕过方案
- 决定是否可"有条件放行"（需产品/业务方签字确认）
- 在发布说明中明确列出"已知限制"

### 7.3 如果外部依赖问题持续（BUG-UAT-003）
- 在用户文档中增加"LLM 服务不稳定时的使用建议"
- 提供 fallback 功能的使用说明
- 监控生产环境 LLM API 的 SLA

---

## 8. 复测完成后的输出

### 8.1 必须更新的文档
1. **UAT_Execution_Log_2026-02-11.md** (Retest 章节):
   - 添加复测日期、执行人、结果汇总
   - 更新用例状态（FAIL → PASS 或 RETEST_FAIL）

2. **UAT_Defects_2026-02-11.md**:
   - 更新缺陷状态（Open → Fixed → Closed）
   - 如果复测失败，添加新缺陷或重新开启原缺陷

3. **最终放行决策文档** (可新建 `UAT_Final_Decision_2026-02-11.md`):
   - Go / Conditional Go / No-Go
   - 放行签署人和日期
   - 已知限制清单

### 8.2 可选的持续改进
- 将本次验收中发现的问题纳入回归测试套件
- 更新 CI/CD pipeline 增加自动化验收门禁
- 完善主手册中的"已知问题与验收口径"章节

---

**文档结束**

## 附录: 快速复测脚本模板

```bash
#!/bin/bash
# UAT Retest Quick Script

echo "=== StockTracker UAT Retest ==="
echo "Date: $(date)"
echo ""

# P0-1: ANA-002 CSV Export
echo "[P0-1] Testing CSV Export..."
curl -s "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=summary" | head -1
curl -s "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=holdings" | head -1
curl -s "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=trades" | head -1
echo ""

# P0-2: KB-002 Search
echo "[P0-2] Testing KB Search..."
curl -s -X POST http://localhost:8001/api/v1/kb/search \
  -H "Content-Type: application/json" \
  -d '{"query":"moving average","mode":"fts"}' | jq '.hits | length'
echo ""

# P1-1: AG-004 Report
echo "[P1-1] Testing Agent Report..."
curl -s -X POST http://localhost:8001/api/v1/agent/backtests/2/report \
  -H "Content-Type: application/json" \
  -d '{"include_kb_citations":false}' --max-time 60 | jq -r '.detail // "SUCCESS"'
echo ""

echo "=== Retest Completed ==="
```
