# StockTracker Backend Server Management

## Overview

The backend server uses a robust process management system to prevent multiple instances from running on the same port. This eliminates issues where multiple processes listen on the same port, which can cause CORS errors and other connectivity problems.

## Features

1. **Port Locking**: Only one server instance can run on a given port
2. **PID File Management**: Tracks running server process via `.server_{port}.pid` file
3. **Automatic Cleanup**: Detects and removes stale PID files
4. **Process Detection**: Identifies processes using the target port
5. **Graceful Shutdown**: Proper cleanup on SIGINT/SIGTERM signals
6. **Force Restart**: Option to kill existing processes and restart

## Starting the Server

### Option 1: Using Batch Script (Windows)
```bash
# Start normally (will fail if port is in use)
start-backend.bat

# Force restart (kills existing processes first)
restart-backend.bat
```

### Option 2: Using Python Script Directly
```bash
cd backend

# Start with default settings (port 8001)
python start_server.py

# Specify custom port
python start_server.py --port 8002

# Force restart (kill existing processes)
python start_server.py --port 8001 --force

# Custom host and port
python start_server.py --host 127.0.0.1 --port 8001
```

## Stopping the Server

### Option 1: Using Batch Script (Windows)
```bash
stop-backend.bat
```

### Option 2: Using Python Script Directly
```bash
cd backend
python stop_server.py --port 8001
```

### Option 3: Keyboard Interrupt
Press `Ctrl+C` in the terminal where the server is running.

## How It Works

### 1. Port Checking
Before starting, the server checks if the port is available:
- Uses socket connection to test port availability
- If port is in use and `--force` is not specified, shows error and exits
- If `--force` is specified, kills all processes using the port

### 2. PID File Locking
```
backend/.server_8001.pid
```
- Contains the process ID of the running server
- Created when server starts
- Removed when server stops gracefully
- Checked for staleness (process no longer exists) on startup

### 3. Process Detection
Uses `psutil` library to:
- Find all processes listening on the target port
- Display process information (PID, name, command line)
- Terminate or force-kill processes as needed

### 4. Graceful Shutdown
Signal handlers ensure proper cleanup:
- Catches SIGINT (Ctrl+C) and SIGTERM signals
- Terminates the server process
- Removes PID file
- Waits up to 5 seconds for graceful shutdown
- Force kills if timeout expires

## Troubleshooting

### Port Already in Use
```
❌ Port 8001 is already in use!

Processes using the port:
  - PID 12345: python.exe - C:\...\uvicorn app.main:app --reload

Options:
  1. Run with --force to kill existing processes
  2. Manually kill the processes
  3. Change the port in config
```

**Solution**: Use force restart:
```bash
python start_server.py --port 8001 --force
```

### Stale PID File
```
⚠️  Stale PID file found (process 12345 not running), removing...
```

This is automatically handled. The server will remove stale PID files and continue.

### Multiple Processes Found
```
⚠️  Found 3 process(es) using port 8001:
   PID 12345: python.exe - uvicorn app.main:app
   PID 12346: python.exe - uvicorn app.main:app
   PID 12347: python.exe - uvicorn app.main:app
```

Use `--force` to kill all processes:
```bash
python start_server.py --port 8001 --force
```

### Access Denied
```
❌ Access denied to process 12345: [WinError 5] Access Denied
```

Run the command prompt or terminal as Administrator on Windows.

## Best Practices

1. **Always use the provided scripts** to start/stop the server
2. **Don't manually run uvicorn** - use `start_server.py` instead
3. **Check the logs** when starting to ensure clean startup
4. **Use `--force` sparingly** - only when you're sure you want to kill existing processes
5. **Monitor the PID file** - if it persists after server stops, something went wrong

## Configuration

The server reads configuration from:
- `backend/app/config.py` - CORS settings, database URL, etc.
- Environment variables (`.env` file)
- Command line arguments (--host, --port, --force)

Current settings:
- Default Host: `0.0.0.0` (all interfaces)
- Default Port: `8001`
- PID File Location: `backend/.server_{port}.pid`

## Files

- `start_server.py` - Server startup with process management
- `stop_server.py` - Server shutdown script
- `start-backend.bat` - Windows batch script to start server
- `stop-backend.bat` - Windows batch script to stop server
- `restart-backend.bat` - Windows batch script to force restart
- `.server_{port}.pid` - Process ID lock file (auto-generated)

## Dependencies

```
psutil>=7.0.0  # Process management library
```

Ensure psutil is installed:
```bash
pip install -r requirements.txt
```
