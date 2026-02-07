from fastapi import APIRouter, Request
from pydantic import BaseModel

router = APIRouter()


class NavEvent(BaseModel):
    path: str
    ts: int | None = None


@router.post("/nav")
async def nav_event(event: NavEvent, request: Request):
    client_host = request.client.host if request.client else "unknown"
    print(f"[NAV] {event.path} from {client_host}", flush=True)
    return {"ok": True}


class ClickEvent(BaseModel):
    path: str
    label: str | None = None
    href: str | None = None
    ts: int | None = None


@router.post("/click")
async def click_event(event: ClickEvent, request: Request):
    client_host = request.client.host if request.client else "unknown"
    label = event.label or "-"
    href = event.href or "-"
    print(f"[CLICK] path={event.path} label={label} href={href} from {client_host}", flush=True)
    return {"ok": True}
