from collections import defaultdict, deque
from typing import Deque, Dict
from time import time

from fastapi import APIRouter, Request
from pydantic import BaseModel


router = APIRouter()


class AnalyticsEvent(BaseModel):
    name: str
    path: str | None = None
    meta: dict | None = None


events: Dict[str, Deque[dict]] = defaultdict(deque)


@router.post("/event")
async def track_event(request: Request, event: AnalyticsEvent):
    entry = {
        "name": event.name,
        "path": event.path,
        "meta": event.meta or {},
        "ts": int(time()),
        "user_id": getattr(request.state, "user_id", None),
    }
    events[event.name].append(entry)
    if len(events[event.name]) > 1000:
        events[event.name].popleft()
    return {"status": "ok"}


@router.get("/summary")
async def analytics_summary():
    return {
        "events": {name: len(items) for name, items in events.items()},
    }
