"""Check /api/v1/agent/health and return non-zero on failure."""
from __future__ import annotations

import argparse
import sys

import httpx


def main() -> int:
    parser = argparse.ArgumentParser(description="Check agent LLM readiness endpoint.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="API base URL")
    parser.add_argument("--probe", action="store_true", help="Enable live LLM probe")
    parser.add_argument("--timeout-seconds", type=float, default=10.0, help="HTTP timeout")
    args = parser.parse_args()

    base = args.base_url.rstrip("/")
    url = f"{base}/api/v1/agent/health"
    params = {"probe": "true"} if args.probe else {}

    try:
        with httpx.Client(timeout=args.timeout_seconds, trust_env=False) as client:
            resp = client.get(url, params=params)
    except Exception as exc:
        print(f"[agent-health] fail request_error={exc}")
        return 2

    body = {}
    try:
        body = resp.json()
    except Exception:
        pass

    ok = resp.status_code == 200 and bool(body.get("ok"))
    detail = body.get("detail", "")
    provider = body.get("provider", "")
    model = body.get("model", "")
    print(
        f"[agent-health] status={resp.status_code} ok={body.get('ok')} "
        f"provider={provider} model={model} detail={detail}"
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
