# StockTracker Backend Server Management

## Overview

Backend startup is managed by scripts in this folder to avoid duplicate server instances and stale port usage.

## Recommended Commands (Windows)

### Start backend

```bat
backend\start-backend.cmd
```

### Start scheduler

```bat
backend\start-scheduler.cmd
```

### Stop backend manually (by port)

```bash
cd backend
python stop_server.py --port 8001
```

## How startup works

1. `start-backend.cmd` ensures `venv\` exists and installs `requirements.txt` if key runtime deps are missing.
2. It picks a free backend port (starting from `8001`) and writes it to `.runtime/backend-port.txt`.
3. It launches `start_server.py --force` so stale/conflicting processes on that port are cleaned before startup.

## PID lock files

- Runtime lock file format: `backend/.server_{port}.pid`
- Lock files are transient runtime artifacts and should not be committed.

## Common troubleshooting

### Backend not reachable from frontend

1. Confirm backend process is running.
2. Check `.runtime/backend-port.txt` for the active port.
3. Verify `frontend/start-frontend.cmd` picked the same port in `VITE_API_URL`.

### Port conflict

- `start_server.py --force` will terminate processes using the selected port and retry startup.

### Environment issues

- Rebuild environment:

```bash
py -3.11 -m venv venv
venv\Scripts\python -m pip install -r backend/requirements.txt
```

## File references

- `backend/start-backend.cmd`
- `backend/start-scheduler.cmd`
- `backend/start_server.py`
- `backend/stop_server.py`
