from fastapi import APIRouter

from app.services.metrics import snapshot

router = APIRouter()


@router.get("/summary")
async def monitoring_summary():
    return {
        "metrics": snapshot(),
    }
