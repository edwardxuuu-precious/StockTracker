"""
Backend server startup script with port management and process locking.
"""
import os
import sys
import signal
import socket
import psutil
import subprocess
from pathlib import Path


class ServerManager:
    """Manages backend server startup with port locking and process cleanup."""

    def __init__(self, host="0.0.0.0", port=8001):
        self.host = host
        self.port = port
        self.pid_file = Path(__file__).parent / f".server_{port}.pid"

    def is_port_in_use(self):
        """Check if port is already in use.

        NOTE:
        Binding with SO_REUSEADDR can produce false negatives on Windows.
        Use active connection probes plus process inspection instead.
        """
        probes = (
            (socket.AF_INET, "127.0.0.1"),
            (socket.AF_INET6, "::1"),
        )
        for family, host in probes:
            try:
                with socket.socket(family, socket.SOCK_STREAM) as s:
                    s.settimeout(0.3)
                    if s.connect_ex((host, self.port)) == 0:
                        return True
            except OSError:
                # Ignore unsupported address families or temporary socket errors.
                pass

        # Fallback: inspect listeners directly.
        return len(self.get_process_using_port()) > 0

    def get_process_using_port(self):
        """Find processes using the specified port."""
        processes = []
        seen_pids = set()
        for conn in psutil.net_connections(kind="inet"):
            if conn.status != "LISTEN":
                continue
            if not conn.laddr or conn.laddr.port != self.port:
                continue
            if conn.pid in (None, 0) or conn.pid in seen_pids:
                continue
            try:
                process = psutil.Process(conn.pid)
                seen_pids.add(conn.pid)
                processes.append({
                    "pid": conn.pid,
                    "name": process.name(),
                    "cmdline": " ".join(process.cmdline())
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        return processes

    def kill_processes_on_port(self):
        """Kill all processes using the port."""
        processes = self.get_process_using_port()
        if not processes:
            return 0

        print(f"[WARN] Found {len(processes)} process(es) using port {self.port}:")
        for proc in processes:
            print(f"   PID {proc['pid']}: {proc['name']} - {proc['cmdline'][:80]}")

        killed = 0
        for proc in processes:
            try:
                process = psutil.Process(proc['pid'])
                print(f"[KILL] Killing process {proc['pid']} ({proc['name']})...")
                process.terminate()
                process.wait(timeout=5)
                killed += 1
            except psutil.TimeoutExpired:
                print(f"[WARN] Force killing process {proc['pid']}...")
                process.kill()
                killed += 1
            except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
                print(f"[ERROR] Failed to kill process {proc['pid']}: {e}")

        return killed

    def read_pid_file(self):
        """Read PID from lock file."""
        if not self.pid_file.exists():
            return None
        try:
            return int(self.pid_file.read_text().strip())
        except (ValueError, IOError):
            return None

    def write_pid_file(self, pid):
        """Write PID to lock file."""
        self.pid_file.write_text(str(pid))

    def remove_pid_file(self):
        """Remove PID lock file."""
        if self.pid_file.exists():
            self.pid_file.unlink()

    def cleanup_stale_pid(self):
        """Remove PID file if process is not running."""
        pid = self.read_pid_file()
        if pid is None:
            return

        try:
            process = psutil.Process(pid)
            if 'python' not in process.name().lower():
                print(f"[WARN] Stale PID file found (process {pid} is not Python), removing...")
                self.remove_pid_file()
        except psutil.NoSuchProcess:
            print(f"[WARN] Stale PID file found (process {pid} not running), removing...")
            self.remove_pid_file()

    def start_server(self, force_restart=False):
        """Start the server with proper cleanup."""
        print(f"[START] Starting StockTracker Backend Server on {self.host}:{self.port}")
        print("=" * 60)

        # Check for stale PID files
        self.cleanup_stale_pid()

        # Check if port is in use
        if self.is_port_in_use():
            if force_restart:
                print(f"[WARN] Port {self.port} is in use. Force restart requested.")
                killed = self.kill_processes_on_port()
                if killed > 0:
                    print(f"[OK] Killed {killed} process(es)")
                    import time
                    time.sleep(1)  # Wait for port to be released
            else:
                print(f"[ERROR] Port {self.port} is already in use!")
                processes = self.get_process_using_port()
                if processes:
                    print("\nProcesses using the port:")
                    for proc in processes:
                        print(f"  - PID {proc['pid']}: {proc['cmdline'][:100]}")
                print("\nOptions:")
                print(f"  1. Run with --force to kill existing processes")
                print(f"  2. Manually kill the processes")
                print(f"  3. Change the port in config")
                return False

        # Verify port is free
        if self.is_port_in_use():
            print(f"[ERROR] Port {self.port} is still in use after cleanup!")
            return False

        print(f"[OK] Port {self.port} is available")
        print("=" * 60)

        # Start uvicorn
        try:
            cmd = [
                sys.executable, "-m", "uvicorn",
                "app.main:app",
                "--host", self.host,
                "--port", str(self.port),
                "--reload",
                "--log-level", "info",
                "--access-log"
            ]

            print(f"[INFO] Command: {' '.join(cmd)}")
            print("=" * 60)

            # Start the process
            process = subprocess.Popen(cmd, cwd=Path(__file__).parent)

            # Save PID
            self.write_pid_file(process.pid)
            print(f"[OK] Server started with PID: {process.pid}")
            print(f"[INFO] PID file: {self.pid_file}")
            print(f"[INFO] Server URL: http://localhost:{self.port}")
            print(f"[INFO] API Docs: http://localhost:{self.port}/docs")
            print("=" * 60)
            print("Press Ctrl+C to stop the server")

            # Setup signal handlers for cleanup
            def cleanup(signum, frame):
                print("\n[STOP] Shutting down server...")
                self.remove_pid_file()
                process.terminate()
                try:
                    process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                print("[OK] Server stopped")
                sys.exit(0)

            signal.signal(signal.SIGINT, cleanup)
            signal.signal(signal.SIGTERM, cleanup)

            # Wait for process
            process.wait()

        except KeyboardInterrupt:
            print("\n[STOP] Interrupted by user")
            self.remove_pid_file()
        except Exception as e:
            print(f"[ERROR] Failed to start server: {e}")
            self.remove_pid_file()
            return False

        return True


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Start StockTracker Backend Server")
    parser.add_argument("--host", default="0.0.0.0", help="Host to bind to")
    parser.add_argument("--port", type=int, default=8001, help="Port to bind to")
    parser.add_argument("--force", action="store_true", help="Force restart by killing existing processes")

    args = parser.parse_args()

    manager = ServerManager(host=args.host, port=args.port)
    success = manager.start_server(force_restart=args.force)

    sys.exit(0 if success else 1)
