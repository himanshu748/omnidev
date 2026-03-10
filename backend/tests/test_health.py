import pytest


@pytest.mark.asyncio
async def test_health(client, coverage_tracker):
    resp = await client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok", "service": "omnidev"}
    coverage_tracker("GET /health")
