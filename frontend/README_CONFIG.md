# 前端配置管理和验证系统

## 🎯 目标

防止端口配置错误导致的 Network Error 和 CORS 问题。

## 🛡️ 防护机制

### 1. 启动前自动检查 ✅

**使用方式:**
```bash
npm run dev  # 自动检查配置,失败则不启动
```

**检查内容:**
- `.env` 文件是否存在
- API URL 端口是否正确(8001)
- 后端服务器是否运行
- 依赖是否已安装

### 2. 独立配置检查工具 ✅

**使用方式:**
```bash
cd frontend
check-config.bat  # Windows
# 或
node scripts/preflight.cjs  # 跨平台
```

### 3. 运行时验证 ✅

应用启动时自动验证并输出配置状态到控制台。

### 4. 增强的错误提示 ✅

Network Error 发生时提供详细的调试步骤。

## 📂 新增文件

```
frontend/
├── scripts/
│   └── preflight.cjs         # 启动前检查脚本
├── src/
│   ├── config/
│   │   └── config.js         # 中心化配置管理
│   ├── services/
│   │   └── api.js           # 增强的API客户端(带验证)
│   └── utils/
│       └── healthCheck.js    # 健康检查工具
├── check-config.bat          # 配置验证批处理脚本
├── .env                      # 环境变量(已修复为8001)
└── .env.example             # 环境变量模板(已修复为8001)
```

## 🚀 使用指南

### 正常启动

```bash
# 1. 启动后端
start-backend.bat

# 2. 启动前端(自动检查)
cd frontend
npm run dev
```

### 如果启动失败

Pre-flight 检查会告诉你具体问题和修复方法:

```
❌ WRONG PORT! API URL is set to port 8000
   Backend server runs on port 8001
   Please update .env file to:
   VITE_API_URL=http://localhost:8001
```

按照提示修复后重新运行 `npm run dev`。

### 手动检查配置

```bash
cd frontend
check-config.bat
```

## 🔧 配置文件

### .env 文件示例

```bash
# 正确配置 ✅
VITE_API_URL=http://localhost:8001

# 错误配置 ❌
VITE_API_URL=http://localhost:8000
```

**重要提醒:**
- 修改 `.env` 后必须重启前端服务器
- 使用 `Ctrl+C` 停止,然后 `npm run dev` 重启

## 📊 验证成功的标志

### 1. 启动时

```
✅ All pre-flight checks PASSED
   You can now start the frontend server.
```

### 2. 浏览器控制台

```
🌐 API Client initialized with baseURL: http://localhost:8001
✅ API Health Check: Backend server is running
```

### 3. Network 标签

API 请求显示:
- URL: `http://localhost:8001/api/v1/portfolios/`
- Status: `200 OK`
- Response Headers 包含: `Access-Control-Allow-Origin: *`

## ⚠️ 常见问题

### Q: Pre-flight 检查失败怎么办?

A: 按照错误提示修复:
1. 检查 `.env` 文件
2. 确保后端在运行
3. 验证端口配置(8001)

### Q: 可以跳过检查吗?

A: 可以但不推荐:
```bash
npm run dev:skip-checks
```

### Q: 修改了 .env 为什么不生效?

A: 必须重启前端服务器:
```bash
# Ctrl+C 停止
npm run dev  # 重新启动
```

### Q: 生产环境怎么配置?

A: 创建 `.env.production`:
```bash
VITE_API_URL=https://api.yourdomain.com
```

## 📚 详细文档

- [完整防护策略](../docs/notes/PREVENTION_STRATEGY.md)
- [Network Error 问题分析](../docs/operations/NETWORK_ERROR_ANALYSIS.md)
- [快速参考](../docs/operations/QUICK_REFERENCE.md)

## ✅ 总结

这个系统从多个层面防止配置错误:

1. ✅ 启动前自动检查 - 防止错误启动
2. ✅ 运行时验证 - 立即发现问题
3. ✅ 清晰的错误提示 - 快速定位和修复
4. ✅ 独立检查工具 - 随时验证配置
5. ✅ 中心化配置 - 统一管理

**再也不会因为端口配置错误而浪费时间调试了!** 🎉
