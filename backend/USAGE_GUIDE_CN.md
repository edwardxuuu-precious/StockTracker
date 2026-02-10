# StockTracker 后端服务器进程管理使用指南

## 概述

后端服务器使用了强大的进程管理系统,可以防止多个实例同时运行在同一端口上。这解决了多进程监听同一端口导致的CORS错误和其他连接问题。

## 核心功能

1. **端口锁定**: 同一端口只能运行一个服务器实例
2. **PID文件管理**: 通过 `.server_{port}.pid` 文件追踪运行中的服务器进程
3. **自动清理**: 检测并删除过期的PID文件
4. **进程检测**: 识别正在使用目标端口的进程
5. **优雅关闭**: 正确处理SIGINT/SIGTERM信号并清理资源
6. **强制重启**: 提供选项终止现有进程并重启

## 启动服务器

### 方式1: 使用批处理脚本 (Windows)
```bash
# 正常启动 (如果端口被占用会失败)
start-backend.bat

# 强制重启 (先终止现有进程)
restart-backend.bat
```

### 方式2: 直接使用Python脚本
```bash
cd backend

# 使用默认设置启动 (端口 8001)
python start_server.py

# 指定自定义端口
python start_server.py --port 8002

# 强制重启 (终止现有进程)
python start_server.py --port 8001 --force

# 自定义主机和端口
python start_server.py --host 127.0.0.1 --port 8001
```

## 停止服务器

### 方式1: 使用批处理脚本 (Windows)
```bash
stop-backend.bat
```

### 方式2: 直接使用Python脚本
```bash
cd backend
python stop_server.py --port 8001
```

### 方式3: 键盘中断
在运行服务器的终端窗口按 `Ctrl+C`

## 工作原理

### 1. 端口检查
启动前,服务器会检查端口是否可用:
- 使用socket绑定测试端口可用性
- 如果端口被占用且未指定 `--force`,显示错误并退出
- 如果指定了 `--force`,终止所有使用该端口的进程

### 2. PID文件锁定
```
backend/.server_8001.pid
```
- 包含运行中服务器的进程ID
- 服务器启动时创建
- 服务器优雅停止时删除
- 启动时检查是否过期(进程已不存在)

### 3. 进程检测
使用 `psutil` 库来:
- 查找监听目标端口的所有进程
- 显示进程信息(PID、名称、命令行)
- 根据需要终止或强制终止进程

### 4. 优雅关闭
信号处理器确保正确清理:
- 捕获 SIGINT (Ctrl+C) 和 SIGTERM 信号
- 终止服务器进程
- 删除PID文件
- 等待最多5秒进行优雅关闭
- 超时后强制终止

## 故障排除

### 端口已被占用
```
[ERROR] Port 8001 is already in use!

Processes using the port:
  - PID 12345: python.exe - C:\...\uvicorn app.main:app --reload

Options:
  1. Run with --force to kill existing processes
  2. Manually kill the processes
  3. Change the port in config
```

**解决方案**: 使用强制重启:
```bash
python start_server.py --port 8001 --force
```

或者使用批处理脚本:
```bash
restart-backend.bat
```

### 过期的PID文件
```
[WARN] Stale PID file found (process 12345 not running), removing...
```

这会自动处理。服务器会删除过期的PID文件并继续。

### 发现多个进程
```
[WARN] Found 3 process(es) using port 8001:
   PID 12345: python.exe - uvicorn app.main:app
   PID 12346: python.exe - uvicorn app.main:app
   PID 12347: python.exe - uvicorn app.main:app
```

使用 `--force` 终止所有进程:
```bash
python start_server.py --port 8001 --force
```

### 访问被拒绝
```
[ERROR] Access denied to process 12345: [WinError 5] Access Denied
```

在Windows上以管理员身份运行命令提示符或终端。

## 最佳实践

1. **始终使用提供的脚本**来启动/停止服务器
2. **不要手动运行uvicorn** - 使用 `start_server.py` 代替
3. **启动时检查日志**确保干净启动
4. **谨慎使用 `--force`** - 只在确定要终止现有进程时使用
5. **监控PID文件** - 如果服务器停止后文件仍然存在,说明出现了问题

## 配置

服务器从以下位置读取配置:
- `backend/app/config.py` - CORS设置、数据库URL等
- 环境变量 (`.env` 文件)
- 命令行参数 (--host, --port, --force)

当前设置:
- 默认主机: `0.0.0.0` (所有网络接口)
- 默认端口: `8001`
- PID文件位置: `backend/.server_{port}.pid`

## 相关文件

- `start_server.py` - 带进程管理的服务器启动脚本
- `stop_server.py` - 服务器停止脚本
- `start-backend.bat` - Windows批处理启动脚本
- `stop-backend.bat` - Windows批处理停止脚本
- `restart-backend.bat` - Windows批处理强制重启脚本
- `.server_{port}.pid` - 进程ID锁文件(自动生成)

## 依赖

```
psutil>=7.0.0  # 进程管理库
```

确保已安装psutil:
```bash
pip install -r requirements.txt
```

## 如何防止多进程问题

这个新系统通过以下机制防止多进程监听同一端口:

1. **启动前检查**: 在启动新服务器之前,检查端口是否已被使用
2. **PID文件锁**: 使用PID文件记录运行中的进程,防止重复启动
3. **自动清理**: 自动检测并清理僵尸进程和过期的PID文件
4. **强制重启选项**: 提供 `--force` 选项来清理所有现有进程并重启
5. **优雅关闭**: 确保服务器停止时正确清理PID文件

这比简单地更改端口更好,因为它:
- ✅ 从根本上解决了多进程问题
- ✅ 提供了可预测的服务器状态
- ✅ 防止了资源泄漏
- ✅ 避免了端口冲突
- ✅ 提供了清晰的错误信息和解决方案

## 常见使用场景

### 场景1: 正常启动
```bash
# 双击 start-backend.bat 或运行:
python backend/start_server.py --port 8001
```

### 场景2: 端口被占用
```bash
# 系统会提示端口被占用,使用强制重启:
python backend/start_server.py --port 8001 --force
```

### 场景3: 开发过程中快速重启
```bash
# 使用提供的重启脚本:
restart-backend.bat
```

### 场景4: 停止服务器
```bash
# 使用停止脚本:
stop-backend.bat

# 或在服务器窗口按 Ctrl+C
```
