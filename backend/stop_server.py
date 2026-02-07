"""
Stop the backend server gracefully.
"""
import sys
import psutil
from pathlib import Path


def stop_server(port=8001):
    """Stop the server running on the specified port."""
    pid_file = Path(__file__).parent / f".server_{port}.pid"

    print(f"[STOP] Stopping server on port {port}...")

    # Try to read PID file
    pid = None
    if pid_file.exists():
        try:
            pid = int(pid_file.read_text().strip())
            print(f"[INFO] Found PID file: {pid}")
        except (ValueError, IOError) as e:
            print(f"[WARN] Could not read PID file: {e}")

    # Find processes using the port
    processes_killed = 0
    for conn in psutil.net_connections():
        if conn.laddr.port == port and conn.status == 'LISTEN':
            try:
                process = psutil.Process(conn.pid)
                print(f"[KILL] Killing process {conn.pid} ({process.name()})...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    processes_killed += 1
                    print(f"[OK] Process {conn.pid} terminated")
                except psutil.TimeoutExpired:
                    print(f"[WARN] Force killing process {conn.pid}...")
                    process.kill()
                    processes_killed += 1
                    print(f"[OK] Process {conn.pid} killed")
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[ERROR] Failed to kill process {conn.pid}: {e}")

    # Kill process from PID file if it exists
    if pid:
        try:
            process = psutil.Process(pid)
            if 'python' in process.name().lower():
                print(f"[KILL] Killing server process {pid}...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    processes_killed += 1
                    print(f"[OK] Server process {pid} terminated")
                except psutil.TimeoutExpired:
                    print(f"[WARN] Force killing server process {pid}...")
                    process.kill()
                    processes_killed += 1
                    print(f"[OK] Server process {pid} killed")
        except psutil.NoSuchProcess:
            print(f"[WARN] Process {pid} not found")
        except psutil.AccessDenied as e:
            print(f"[ERROR] Access denied to process {pid}: {e}")

    # Remove PID file
    if pid_file.exists():
        pid_file.unlink()
        print(f"[INFO] Removed PID file")

    if processes_killed > 0:
        print(f"[OK] Stopped {processes_killed} process(es)")
    else:
        print("[INFO] No processes found to stop")

    return processes_killed > 0


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Stop StockTracker Backend Server")
    parser.add_argument("--port", type=int, default=8001, help="Port the server is running on")

    args = parser.parse_args()

    success = stop_server(port=args.port)
    sys.exit(0 if success else 1)
