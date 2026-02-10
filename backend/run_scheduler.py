"""Simple ingestion scheduler for local market data updates."""
from __future__ import annotations

import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import SessionLocal, init_db
from app.services.market_data_providers import AkshareMarketDataProvider, UsYFinanceMarketDataProvider
from app.services.market_data_service import MarketDataService

DEFAULT_CONFIG = Path(__file__).resolve().parent / "config" / "ingestion_jobs.json"
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_HEARTBEAT_PATH = PROJECT_ROOT / ".runtime" / "scheduler" / "heartbeat.json"
DEFAULT_REPORT_DIR = PROJECT_ROOT / ".runtime" / "scheduler" / "reports"


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _truthy(value: str | None) -> bool:
    return str(value or "").strip().lower() in {"1", "true", "yes", "on"}


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _post_alert(webhook_url: str, payload: dict) -> bool:
    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        webhook_url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=5):
            return True
    except Exception:
        return False


def _cleanup_reports(report_dir: Path, keep_count: int) -> None:
    keep = max(int(keep_count), 1)
    reports = sorted(report_dir.glob("cycle_*.json"), key=lambda item: item.stat().st_mtime, reverse=True)
    for stale in reports[keep:]:
        stale.unlink(missing_ok=True)


def load_jobs(config_path: Path) -> list[dict]:
    if not config_path.exists():
        print(f"[WARN] Config not found: {config_path}")
        return []
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return data.get("jobs", [])


def run_job(db: Session, service: MarketDataService, job: dict) -> dict:
    name = str(job.get("name", "job"))
    market = str(job.get("market", "CN")).upper()
    interval = str(job.get("interval", "1m")).lower()
    provider = job.get("provider")
    symbols = [str(s).strip().upper() for s in job.get("symbols", []) if str(s).strip()]
    start = job.get("start")
    end = job.get("end")
    started_at = _utcnow()
    summary = {
        "name": name,
        "market": market,
        "interval": interval,
        "symbols": symbols,
        "attempted": len(symbols),
        "succeeded": 0,
        "failed": 0,
        "ingested_total": 0,
        "errors": [],
        "started_at": started_at.isoformat(),
        "finished_at": None,
    }
    if isinstance(start, str) and start:
        start = datetime.fromisoformat(start.replace("Z", "+00:00"))
    else:
        start = None if start is None else start
    if isinstance(end, str) and end:
        end = datetime.fromisoformat(end.replace("Z", "+00:00"))
    else:
        end = None if end is None else end

    for symbol in symbols:
        try:
            ingested = service.ingest_history(
                db=db,
                symbol=symbol,
                market=market,
                interval=interval,
                start=start,
                end=end,
                provider_name=provider,
            )
            summary["succeeded"] += 1
            summary["ingested_total"] += int(ingested or 0)
            print(f"[OK] {symbol} {market} {interval} ingested={ingested}")
        except Exception as exc:
            summary["failed"] += 1
            summary["errors"].append({"symbol": symbol, "message": str(exc)[:300]})
            print(f"[ERR] {symbol} {market} {interval} {exc}")
    summary["finished_at"] = _utcnow().isoformat()
    return summary


def main() -> None:
    get_settings()
    init_db()
    config_path = Path(os.getenv("INGESTION_JOBS_PATH", str(DEFAULT_CONFIG)))
    heartbeat_path = Path(os.getenv("SCHEDULER_HEARTBEAT_PATH", str(DEFAULT_HEARTBEAT_PATH)))
    report_dir = Path(os.getenv("SCHEDULER_REPORT_DIR", str(DEFAULT_REPORT_DIR)))
    alert_webhook = str(os.getenv("SCHEDULER_ALERT_WEBHOOK", "")).strip()
    report_retention = int(os.getenv("SCHEDULER_REPORT_RETENTION_COUNT", "200"))
    run_once = _truthy(os.getenv("SCHEDULER_RUN_ONCE", "false"))
    poll_seconds = int(os.getenv("SCHEDULER_POLL_SECONDS", "30"))
    jobs = load_jobs(config_path)
    if not jobs:
        _write_json(
            heartbeat_path,
            {
                "status": "idle_no_jobs",
                "timestamp_utc": _utcnow().isoformat(),
                "config_path": str(config_path),
                "jobs": 0,
            },
        )
        print("[WARN] No ingestion jobs configured.")
        return

    service = MarketDataService(
        providers=[AkshareMarketDataProvider(), UsYFinanceMarketDataProvider()],
    )
    last_run: dict[str, datetime] = {}

    print("[OK] Ingestion scheduler started.")
    while True:
        now = _utcnow()
        cycle_jobs: list[dict] = []
        for job in jobs:
            name = str(job.get("name", "job"))
            every = int(job.get("run_every_minutes", 60))
            previous = last_run.get(name)
            if previous is None or (now - previous).total_seconds() >= every * 60:
                with SessionLocal() as db:
                    cycle_jobs.append(run_job(db, service, job))
                last_run[name] = now

        total_attempted = sum(int(item["attempted"]) for item in cycle_jobs)
        total_failed = sum(int(item["failed"]) for item in cycle_jobs)
        total_succeeded = sum(int(item["succeeded"]) for item in cycle_jobs)
        cycle_status = "degraded" if total_failed else "ok"
        cycle_payload = {
            "timestamp_utc": now.isoformat(),
            "status": cycle_status,
            "jobs_executed": len(cycle_jobs),
            "symbols_attempted": total_attempted,
            "symbols_succeeded": total_succeeded,
            "symbols_failed": total_failed,
            "job_results": cycle_jobs,
        }

        stamp = now.strftime("%Y%m%dT%H%M%SZ")
        cycle_report_path = report_dir / f"cycle_{stamp}.json"
        _write_json(cycle_report_path, cycle_payload)
        _cleanup_reports(report_dir, report_retention)
        _write_json(
            heartbeat_path,
            {
                "status": cycle_status,
                "timestamp_utc": now.isoformat(),
                "config_path": str(config_path),
                "last_cycle_report": str(cycle_report_path),
                "jobs_executed": len(cycle_jobs),
                "symbols_failed": total_failed,
            },
        )

        if total_failed and alert_webhook:
            alert_ok = _post_alert(
                alert_webhook,
                {
                    "event": "scheduler_cycle_failed",
                    "timestamp_utc": now.isoformat(),
                    "jobs_executed": len(cycle_jobs),
                    "symbols_failed": total_failed,
                    "last_cycle_report": str(cycle_report_path),
                },
            )
            print(f"[{'OK' if alert_ok else 'WARN'}] alert webhook {'sent' if alert_ok else 'failed'}")

        if run_once:
            break
        time.sleep(max(poll_seconds, 1))


if __name__ == "__main__":
    main()
