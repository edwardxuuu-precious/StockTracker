# Stop Doing - 问题边界与约束

## 📋 文档说明

本文档记录开发过程中遇到的问题、试错经验和解决方案,作为未来开发的边界约束,避免重复犯错。

**更新原则:**
- 每遇到问题立即记录
- 记录问题根因而非表象
- 记录解决方案和预防措施
- 定期回顾和更新

---

## 🚫 技术选择约束

### ❌ 不要使用默认导出和命名导出混用

**问题描述:**
```javascript
// portfolioAPI.js
export default api;  // 默认导出

// EditPortfolioPage.jsx
import { portfolioAPI } from '../services/portfolioAPI';  // 错误:按命名导入
```

**错误信息:**
```
Uncaught SyntaxError: The requested module '/src/services/portfolioAPI.js'
does not provide an export named 'portfolioAPI'
```

**根本原因:**
- 默认导出使用 `export default`
- 命名导出使用 `export const name`
- 两者不能混用,导入方式不同

**正确做法:**
```javascript
// 方式1: 使用默认导出+默认导入
export default api;
import portfolioAPI from '../services/portfolioAPI';

// 方式2: 使用命名导出+命名导入
export const portfolioAPI = api;
import { portfolioAPI } from '../services/portfolioAPI';
```

**预防措施:**
- ✅ 统一使用默认导出(推荐)
- ✅ 或统一使用命名导出
- ✅ 团队约定统一规范
- ✅ ESLint规则检查

**已解决:** ✅ 2026-02-04

---

### ❌ 不要忘记导入使用的图标

**问题描述:**
```javascript
// PortfoliosPage.jsx
import { Plus, TrendingUp, TrendingDown, Trash2 } from 'lucide-react';

// 但在代码中使用了 Briefcase 图标
<Briefcase className="h-8 w-8" />
```

**错误信息:**
```
Uncaught ReferenceError: Briefcase is not defined
```

**根本原因:**
- 使用了未导入的组件/变量
- React将其视为undefined
- JSX无法渲染undefined

**正确做法:**
```javascript
import { Plus, TrendingUp, TrendingDown, Trash2, Briefcase } from 'lucide-react';
```

**预防措施:**
- ✅ 使用TypeScript (编译时检查)
- ✅ 使用ESLint no-undef规则
- ✅ IDE自动导入提示
- ✅ 代码审查

**已解决:** ✅ 2026-02-04

---

### ❌ 不要遗漏API URL的尾部斜杠

**问题描述:**
```javascript
// portfolioAPI.js
export const getPortfolios = async () => {
  const response = await api.get('/api/v1/portfolios');  // 缺少尾部斜杠
  return response.data;
};
```

**错误表现:**
- Network显示 `307 Temporary Redirect`
- Redirect时丢失CORS头
- 导致CORS错误

**根本原因:**
- FastAPI自动将 `/api/v1/portfolios` 重定向到 `/api/v1/portfolios/`
- 307重定向不会携带CORS头
- 浏览器CORS预检失败

**正确做法:**
```javascript
export const getPortfolios = async () => {
  const response = await api.get('/api/v1/portfolios/');  // 添加尾部斜杠
  return response.data;
};
```

**预防措施:**
- ✅ 统一API规范要求尾部斜杠
- ✅ API测试包含URL格式检查
- ✅ 文档明确说明
- ✅ 代码生成工具自动添加

**已解决:** ✅ 2026-02-04

---

### ❌ 不要让.env覆盖代码的正确配置

**问题描述:**
```javascript
// api.js
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001';

// 但 .env 文件中
VITE_API_URL=http://localhost:8000  // 错误的端口
```

**错误表现:**
- 前端请求发送到8000端口
- 后端运行在8001端口
- 导致连接失败和CORS错误

**根本原因:**
- Vite环境变量优先级高于代码默认值
- `.env`文件配置错误但被优先使用
- 开发者以为代码中的默认值会生效

**正确做法:**
```bash
# .env
VITE_API_URL=http://localhost:8001  # 确保端口正确
```

**预防措施:**
- ✅ 启动前自动检查配置(Pre-flight)
- ✅ 运行时验证配置并警告
- ✅ .env.example保持最新
- ✅ 文档明确说明优先级
- ✅ 配置错误阻止启动

**已解决:** ✅ 2026-02-06

---

### ❌ 不要使用emoji在Windows中文环境

**问题描述:**
```python
# stop_server.py
print(f"🛑 Stopping server on port {port}...")
```

**错误信息:**
```
UnicodeEncodeError: 'gbk' codec can't encode character '\U0001f6d1'
in position 0: illegal multibyte sequence
```

**根本原因:**
- Windows中文环境默认使用GBK编码
- Emoji是Unicode字符,GBK无法编码
- Python print默认使用系统编码

**正确做法:**
```python
print(f"[STOP] Stopping server on port {port}...")  # 使用ASCII字符
```

**预防措施:**
- ✅ 避免在终端输出中使用emoji
- ✅ 使用ASCII字符和符号
- ✅ 或设置环境变量 `PYTHONIOENCODING=utf-8`
- ✅ 测试时包含中文Windows环境

**已解决:** ✅ 2026-02-06

---

## 🚫 架构设计约束

### ❌ 不要手动管理多个后端进程

**问题描述:**
手动启动多个后端实例导致多个进程监听同一端口。

**问题表现:**
```bash
# 发现5个进程同时监听8000端口
PID: 70300, 71096, 51936, 71012, 17100
```

**导致问题:**
- CORS配置不一致
- 请求随机分配到不同进程
- 部分进程配置错误
- 无法正确终止所有进程

**根本原因:**
- 缺少进程管理机制
- 无PID文件锁定
- 无端口占用检查
- 手动启动容易重复

**正确做法:**
实现完整的进程管理系统:
1. 启动前检查端口
2. 使用PID文件锁定
3. 自动清理僵尸进程
4. 提供管理脚本

**预防措施:**
- ✅ 使用start_server.py启动
- ✅ 使用stop_server.py停止
- ✅ 使用restart_backend.bat重启
- ✅ 不要手动运行uvicorn

**已解决:** ✅ 2026-02-06

---

### ❌ 不要跳过配置验证直接启动

**问题描述:**
配置错误(如端口错误)但仍能启动,导致后续难以排查。

**问题表现:**
- 启动成功但功能异常
- 错误提示不明确
- 浪费时间调试

**根本原因:**
- 缺少启动前检查
- 缺少运行时验证
- 错误发现太晚

**正确做法:**
实现多层配置验证:
1. Pre-flight启动前检查
2. 运行时配置验证
3. API客户端验证
4. 错误详细提示
5. 独立验证工具

**预防措施:**
- ✅ 使用 `npm run dev` (带检查)
- ✅ 不使用 `npm run dev:skip-checks`
- ✅ 配置错误阻止启动
- ✅ 定期运行 `check-config.bat`

**已解决:** ✅ 2026-02-06

---

### ❌ 不要在CORS错误中迷失

**问题描述:**
看到CORS错误就认为是CORS配置问题,实际可能是其他原因。

**误导性错误:**
```
Access to XMLHttpRequest has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present
```

**实际原因可能是:**
1. 后端未运行
2. 端口配置错误
3. URL拼写错误
4. 网络连接问题
5. 307重定向问题

**排查顺序:**
1. ✅ 先检查后端是否运行
2. ✅ 检查端口配置
3. ✅ 检查URL是否正确
4. ✅ 检查Network返回状态
5. ✅ 最后才检查CORS配置

**预防措施:**
- ✅ 增强错误提示(包含URL、端口)
- ✅ 提供完整排查步骤
- ✅ Pre-flight检查后端连接
- ✅ 文档说明常见误区

**已记录:** ✅ 2026-02-06

---

## 🚫 开发流程约束

### ❌ 不要在未读取文件的情况下编辑

**问题描述:**
尝试编辑文件但工具提示 "File has not been read yet"

**正确流程:**
```
1. Read 文件
2. Edit 文件
```

**预防措施:**
- ✅ 编辑前先读取
- ✅ 即使认为知道内容也要读取
- ✅ 避免假设文件内容

**已遵守:** ✅ 全程

---

### ❌ 不要修改.env后忘记重启

**问题描述:**
修改了 `frontend/.env` 但前端仍使用旧配置。

**根本原因:**
- Vite在启动时读取.env
- 修改后不会自动重新加载
- 需要重启前端服务器

**正确流程:**
```bash
1. 修改 .env 文件
2. Ctrl+C 停止前端
3. npm run dev 重启前端
```

**预防措施:**
- ✅ 文档说明需要重启
- ✅ Pre-flight检查会读取最新配置
- ✅ 错误提示中包含重启提醒

**已记录:** ✅ 2026-02-06

---

### ❌ 不要同时开发多个功能

**问题描述:**
同时开发多个功能导致代码混乱,难以追踪问题。

**正确做法:**
- ✅ 一次专注一个TODO
- ✅ 完成后再开始下一个
- ✅ 每个功能独立测试
- ✅ 及时提交代码

**优先级管理:**
1. P0 - 紧急且重要(优先完成)
2. P1 - 重要不紧急(计划完成)
3. P2 - 紧急不重要(选择性完成)
4. P3 - 不紧急不重要(暂不实施)

**已遵守:** ✅ 全程

---

## 🚫 代码质量约束

### ❌ 不要过度优化

**说明:**
在功能未完成时就开始优化性能、抽象组件等。

**问题:**
- 浪费时间
- 增加复杂度
- 可能优化方向错误

**原则:**
1. 先完成功能
2. 再优化性能
3. 遵循YAGNI(You Aren't Gonna Need It)

**例外:**
- 明显的性能问题
- 明显的代码重复

**已遵守:** ✅ 全程

---

### ❌ 不要跳过错误处理

**说明:**
为了快速完成功能而跳过错误处理。

**必须的错误处理:**
- ✅ API调用失败
- ✅ 表单验证失败
- ✅ 网络连接失败
- ✅ 数据格式错误

**错误处理要求:**
- 友好的用户提示
- 详细的日志记录
- 适当的降级策略
- 清晰的恢复路径

**已遵守:** ✅ 全程

---

### ❌ 不要使用magic number

**问题代码:**
```javascript
if (portfolios.length > 10) {  // 10是什么?
  // ...
}
```

**正确做法:**
```javascript
const MAX_PORTFOLIOS_DISPLAY = 10;
if (portfolios.length > MAX_PORTFOLIOS_DISPLAY) {
  // ...
}
```

**预防措施:**
- ✅ 使用常量定义
- ✅ 命名清晰表达意图
- ✅ 添加注释说明

**待改进:** ⚠️ 需要Code Review检查

---

## 🚫 技术债务清单

### 需要补充的测试

**单元测试:**
- [ ] 前端组件测试
- [ ] 工具函数测试
- [ ] Store测试

**集成测试:**
- [ ] API端点测试
- [ ] 端到端测试

**性能测试:**
- [ ] 大数据量测试
- [ ] 并发测试

**计划:** Phase 2 完成

---

### 需要优化的代码

**配置管理:**
- [ ] 环境变量类型定义
- [ ] 配置验证规则完善

**错误处理:**
- [ ] 统一错误码
- [ ] 错误日志格式

**代码规范:**
- [ ] ESLint配置
- [ ] Prettier配置
- [ ] Git Hooks

**计划:** 逐步完善

---

## 📝 经验总结

### 成功经验

1. **多层防御思想**
   - 从多个角度防止问题
   - 启动前、运行时、错误时
   - 效果显著

2. **清晰的错误信息**
   - 明确指出问题
   - 提供解决步骤
   - 大幅减少调试时间

3. **完善的文档**
   - 降低理解成本
   - 便于协作
   - 易于维护

4. **自动化优先**
   - 减少人工操作
   - 避免人为错误
   - 提高效率

### 失败教训

1. **假设配置正确**
   - 应该验证而非假设
   - 配置错误很难发现
   - 自动检查是必须的

2. **忽视环境差异**
   - Windows和Linux不同
   - 中文和英文环境不同
   - 需要考虑兼容性

3. **错误信息不够详细**
   - 初期错误提示太简单
   - 排查浪费大量时间
   - 详细提示非常重要

---

## 🎯 下次注意

### 新功能开发时

1. **设计阶段:**
   - [ ] 考虑错误场景
   - [ ] 考虑边界条件
   - [ ] 考虑性能影响
   - [ ] 考虑兼容性

2. **开发阶段:**
   - [ ] 先读取再编辑
   - [ ] 及时测试验证
   - [ ] 添加错误处理
   - [ ] 记录遇到的问题

3. **测试阶段:**
   - [ ] 正常场景测试
   - [ ] 异常场景测试
   - [ ] 边界条件测试
   - [ ] 性能测试

4. **文档阶段:**
   - [ ] 更新使用文档
   - [ ] 更新API文档
   - [ ] 记录注意事项
   - [ ] 更新Stop_Doing

---

## 📅 定期回顾

**回顾频率:** 每周
**回顾内容:**
- 本周遇到的新问题
- 是否有重复犯错
- 预防措施是否有效
- 需要补充的约束

**下次回顾:** 2026-02-13

---

**最后更新:** 2026-02-06
**维护者:** Claude
**版本:** 1.0
