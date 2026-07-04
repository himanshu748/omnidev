import pytest


@pytest.mark.asyncio
async def test_health(client, coverage_tracker):
    resp = await client.get("/health")
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["status"] == "ok"
    assert payload["service"] == "omnidev"
    assert payload["ai_provider"] in {"gemini", "ollama"}
    assert isinstance(payload["ai_model"], str)
    coverage_tracker("GET /health")
