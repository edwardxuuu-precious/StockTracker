from fastapi import APIRouter, Query, Request
from pydantic import BaseModel

from ...services.agent_report_observability import get_agent_report_metrics

router = APIRouter()


class NavEvent(BaseModel):
    path: str
    ts: int | None = None


@router.post("/nav")
async def nav_event(event: NavEvent, request: Request):
    client_host = request.client.host if request.client else "unknown"
    safe_path = event.path.split("?", maxsplit=1)[0][:120]
    print(f"[NAV] path={safe_path} from {client_host}", flush=True)
    return {"ok": True}


class ClickEvent(BaseModel):
    path: str
    label: str | None = None
    href: str | None = None
    ts: int | None = None


@router.post("/click")
async def click_event(event: ClickEvent, request: Request):
    client_host = request.client.host if request.client else "unknown"
    safe_path = event.path.split("?", maxsplit=1)[0][:120]
    has_label = bool(event.label)
    has_href = bool(event.href)
    print(
        f"[CLICK] path={safe_path} has_label={has_label} has_href={has_href} "
        f"from {client_host}",
        flush=True,
    )
    return {"ok": True}


@router.get("/agent-report-metrics")
async def agent_report_metrics(window: int = Query(default=200, ge=1, le=1000)):
    """Return in-memory metrics for agent report reliability."""
    return get_agent_report_metrics(window=window)
