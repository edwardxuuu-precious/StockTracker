# StockTracker UAT 缺陷台账

**验收日期**: 2026-02-11
**关联验收日志**: docs/QA/UAT_Execution_Log_2026-02-11.md

---

## 缺陷汇总

| Defect ID | 关联用例 | 严重级别 | 状态 | 阻塞放行 |
|-----------|---------|---------|------|---------|
| BUG-UAT-001 | ANA-002 | P0 | Open | ✅ YES |
| BUG-UAT-002 | KB-002 | P0 | Open | ✅ YES |
| BUG-UAT-003 | AG-004 | P0 | Open | ⚠️ External Dependency |

---

## BUG-UAT-001: CSV 导出功能未区分 report_type

### 基本信息
- **Defect ID**: BUG-UAT-001
- **关联用例**: ANA-002 (CSV 导出)
- **严重级别**: P0 (影响数据导出完整性)
- **发现时间**: 2026-02-11 04:47 UTC
- **当前状态**: Open

### 现象描述
用户调用 `/api/v1/analytics/portfolios/{id}/export` 端点时，无论 `report_type` 参数为 `summary`、`holdings` 还是 `trades`，返回的 CSV 内容完全一致，均为 summary 格式的汇总数据。

### 稳定复现步骤
1. 创建组合并执行至少一笔交易（确保有 holdings 和 trades 数据）
2. 调用以下三个导出请求：
   ```bash
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=summary" -o summary.csv
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=holdings" -o holdings.csv
   curl "http://localhost:8001/api/v1/analytics/portfolios/1/export?report_type=trades" -o trades.csv
   ```
3. 对比三个文件内容

### 实际结果
三个文件的 CSV header 和内容完全相同：
```csv
portfolio_id,portfolio_name,initial_capital,cash_balance,holdings_market_value,current_value,total_return,total_return_pct,realized_pnl,unrealized_pnl,active_holdings,total_trades,exported_at
1,UAT_Test_Portfolio_2,50000.00,43998.00,6000.00,49998.00,-2.00,-0.0040,0.00,-2.00,1,1,2026-02-11T05:47:52Z
```

### 期望结果
- `report_type=summary`: 返回组合汇总数据（当前实际返回）
- `report_type=holdings`: 返回持仓明细（应包含 symbol, quantity, average_cost, current_price, market_value, unrealized_pnl 等字段）
- `report_type=trades`: 返回交易记录（应包含 trade_id, symbol, action, quantity, price, commission, amount, realized_pnl, trade_time 等字段）

### 影响范围
- 用户无法导出持仓明细和交易记录的 CSV 报表
- 影响数据分析和外部系统集成
- 主手册第 4.5 节声明的导出功能不完整

### 临时绕过方案
用户可直接调用以下 API 获取 JSON 数据并自行转换为 CSV：
- 持仓明细: `GET /api/v1/portfolios/{id}` (从 holdings 字段提取)
- 交易记录: `GET /api/v1/portfolios/{id}/trades`

### 建议修复方向
1. 检查 `backend/app/routes/analytics.py` 中的 export 端点实现
2. 确认 `report_type` 参数是否被正确解析和路由
3. 实现三种导出类型的不同 CSV 生成逻辑：
   - `summary`: 调用 analytics summary 逻辑并格式化为 CSV
   - `holdings`: 从 portfolio.holdings 提取字段并格式化
   - `trades`: 从 portfolio_trades 表查询并格式化
4. 添加单元测试覆盖三种导出类型

### 预期修复工作量
- 代码修改: 1-2 小时（实现条件分支和 CSV 格式化）
- 测试验证: 30 分钟

---

## BUG-UAT-002: 知识库检索返回空结果

### 基本信息
- **Defect ID**: BUG-UAT-002
- **关联用例**: KB-002 (检索命中)
- **严重级别**: P0 (影响知识库核心功能)
- **发现时间**: 2026-02-11 04:38 UTC
- **当前状态**: Open

### 现象描述
用户成功调用 `/api/v1/kb/ingest-text` 入库文本内容（返回 `chunk_count=1`），但随后使用任何查询词（包括文档中的精确关键词）调用 `/api/v1/kb/search` 时，均返回空的 `hits=[]`。

### 稳定复现步骤
1. 入库测试文本：
   ```bash
   curl -X POST http://localhost:8001/api/v1/kb/ingest-text \
     -F 'content=This is a UAT test knowledge base document about trading strategies. Moving average strategies are commonly used.' \
     -F 'title=UAT_Test_Doc' \
     -F 'source_type=text' \
     -F 'source_name=uat_test.txt'
   ```
   返回: `{"document": {...}, "chunk_count": 1}`

2. 验证文档已入库：
   ```bash
   curl http://localhost:8001/api/v1/kb/documents
   ```
   返回: 包含 id=1 的文档

3. 执行检索（尝试多种模式和关键词）：
   ```bash
   # 尝试 1: hybrid 模式 + 精确关键词
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"moving average","mode":"hybrid","max_results":10}'

   # 尝试 2: fts 模式 + 通用词
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"trading","mode":"fts","max_results":10}'

   # 尝试 3: recall 策略放宽治理
   curl -X POST http://localhost:8001/api/v1/kb/search \
     -H "Content-Type: application/json" \
     -d '{"query":"UAT","mode":"fts","governance_policy":"recall"}'
   ```

### 实际结果
所有检索请求均返回：
```json
{
  "query": "...",
  "hits": []
}
```

### 期望结果
至少应返回包含查询词的 chunk 命中，例如：
```json
{
  "query": "moving average",
  "hits": [
    {
      "chunk_id": 1,
      "document_id": 1,
      "content": "...Moving average strategies...",
      "score": 0.85,
      "reference_id": "...",
      "confidence": "high",
      "source_name": "uat_test.txt"
    }
  ]
}
```

### 影响范围
- 知识库检索功能完全不可用
- 影响 Agent 报告生成时的 KB citations
- 主手册第 4.9 节声明的检索能力无法验证

### 可能原因假设
1. **FTS 索引未创建**: chunk 表的 FTS 虚拟表可能未正确初始化
2. **Chunk 切分失败**: ingest-text 虽然返回 chunk_count=1，但实际未写入 chunk 表
3. **检索逻辑错误**: search 服务的查询构造或结果映射有 bug
4. **治理过滤过严**: governance 逻辑可能错误地过滤掉了所有结果

### 临时绕过方案
暂无有效绕过方案。用户需等待修复后才能使用 KB 检索功能。

### 建议修复方向
1. **验证数据完整性**:
   ```sql
   SELECT COUNT(*) FROM chunks WHERE document_id = 1;
   SELECT * FROM chunks_fts WHERE chunks_fts MATCH 'moving';
   ```

2. **检查 ingest 逻辑**:
   - 确认 `backend/app/services/kb/ingestion.py` 中的 chunk 切分和持久化逻辑
   - 验证 FTS 表的 insert trigger 是否正常工作

3. **检查 search 逻辑**:
   - 确认 `backend/app/services/kb/search.py` 中的查询构造
   - 调试 hybrid/fts/vector 三种模式的查询执行路径
   - 验证 governance filter 的裁剪逻辑是否过于激进

4. **添加调试日志**:
   - 在 search 服务中添加中间步骤日志（原始查询结果数、治理过滤前后数量）

5. **补充集成测试**:
   - 添加 end-to-end 测试覆盖 ingest → search 完整流程

### 预期修复工作量
- 问题定位: 1-2 小时（需要数据库调试和日志分析）
- 代码修改: 1-3 小时（取决于根本原因）
- 测试验证: 1 小时

---

## BUG-UAT-003: Agent 报告生成 LLM 超时

### 基本信息
- **Defect ID**: BUG-UAT-003
- **关联用例**: AG-004 (Agent 复盘报告)
- **严重级别**: P0 (影响 Agent 高级功能)
- **发现时间**: 2026-02-11 04:39 UTC
- **当前状态**: Open (External Dependency)

### 现象描述
用户调用 `/api/v1/agent/backtests/{backtest_id}/report` 生成回测复盘报告时，请求持续超时（30-60 秒后返回错误）。错误信息为 `"LLM is required for AI backtest insights: Request timed out."`

### 稳定复现步骤
1. 确保 backtest 已完成（例如 backtest_id=2）
2. 调用报告生成：
   ```bash
   curl -X POST http://localhost:8001/api/v1/agent/backtests/2/report \
     -H "Content-Type: application/json" \
     -d '{"include_kb_citations":true}' \
     --max-time 60
   ```

### 实际结果
- 请求超时（45-60 秒）
- 返回: `{"detail": "LLM is required for AI backtest insights: Request timed out."}`
- 尝试简化参数（`include_kb_citations=false`）仍然超时

### 期望结果
返回 markdown 格式的复盘报告，包含：
- 量化指标解读
- 策略优化建议
- 可选的 KB citations

### 影响范围
- Agent 报告生成功能不可用
- 不影响其他确定性功能（组合管理、回测执行、策略生成、自动调参）
- 主手册第 4.10 节声明的报告生成能力无法完整验证

### 根本原因分析
**外部依赖问题**（非代码缺陷）:
1. **LLM API 网络延迟**: DeepSeek API 当前可能处于高负载或网络拥堵状态
2. **健康检查通过但调用超时**: `/api/v1/agent/health` 返回 `ok=true` 和 `configured=true`，说明配置正确，但实际调用时超时
3. **其他 LLM 功能正常**: AG-002 (策略生成) 成功调用 LLM 并返回结果，说明 LLM 连接可用但不稳定

### 临时绕过方案
1. **使用确定性报告**（如果后端支持 fallback）:
   - 修改后端配置允许在 LLM 超时时返回基于规则的报告

2. **异步报告生成**（需后端支持）:
   - 将报告生成改为异步任务，用户轮询结果

3. **稍后重试**:
   - 在网络条件改善后重新调用

### 建议修复方向
**短期**（应急措施）:
1. 增加 LLM 请求的 timeout 配置（从默认 30 秒提升到 90-120 秒）
2. 添加重试机制（exponential backoff，最多 3 次）
3. 实现 fallback 逻辑：LLM 超时时返回纯量化规则建议（不包含 LLM 生成的文本）

**中期**（架构优化）:
1. 将报告生成改为异步任务（使用消息队列或 Celery）
2. 在前端提供"生成中"状态和轮询机制
3. 增加 LLM 响应缓存（相同 backtest_id 的报告可缓存 1 小时）

**长期**（多 provider 容灾）:
1. 支持多个 LLM provider（OpenRouter, OpenAI, 本地模型）
2. 实现自动 failover（主 provider 失败时切换到备用）

### 是否阻塞放行
**不阻塞**，理由：
1. 这是外部依赖（DeepSeek API）的稳定性问题，非代码缺陷
2. 其他核心功能（组合管理、回测、策略生成、调参）均正常
3. 用户可通过查看 backtest 结果的量化指标自行分析，不完全依赖 LLM 报告

**建议**:
- 在发布说明中标注"报告生成功能依赖外部 LLM 服务，网络不稳定时可能超时"
- 优先实现短期修复方案（增加 timeout 和 fallback）

### 预期修复工作量
- **短期修复** (timeout + retry + fallback): 2-3 小时
- **中期优化** (异步任务): 1-2 天
- **长期容灾** (多 provider): 3-5 天

---

## 缺陷修复优先级建议

1. **BUG-UAT-001** (CSV 导出): 立即修复（阻塞放行，工作量小）
2. **BUG-UAT-002** (KB 检索): 立即修复（阻塞放行，需深入调试）
3. **BUG-UAT-003** (LLM 超时): 实施短期修复（不阻塞但影响用户体验）

---

## 附录: 其他观察到的问题（非缺陷）

### OBS-001: 前端中文乱码
- **现象**: 分析页 trend 数据的 label 字段出现乱码（如 `"鏼憆돧킋"`）
- **严重级别**: P1 (可用性问题，不影响核心计算)
- **状态**: 已知问题（主手册 KN-001）
- **建议**: 检查前端/后端的编码一致性

### OBS-002: 组合删除后 ID 复用
- **现象**: 删除 portfolio id=1 后，新建组合仍使用 id=1
- **严重级别**: P2 (数据库行为，不影响功能正确性)
- **状态**: SQLite AUTOINCREMENT 默认行为
- **建议**: 如需避免 ID 复用，需修改表定义

---

**文档结束**
