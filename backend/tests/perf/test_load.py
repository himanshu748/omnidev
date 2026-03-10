import asyncio
import json
import pathlib
import statistics
import time

import pytest


@pytest.mark.asyncio
async def test_health_load(client):
    durations = []

    async def hit():
        start = time.perf_counter()
        resp = await client.get("/health")
        durations.append(time.perf_counter() - start)
        assert resp.status_code == 200

    await asyncio.gather(*[hit() for _ in range(50)])
    p95 = statistics.quantiles(durations, n=20)[-1]
    report_dir = pathlib.Path("test-results")
    report_dir.mkdir(exist_ok=True)
    payload = {
        "endpoint": "GET /health",
        "requests": len(durations),
        "p50_ms": round(statistics.median(durations) * 1000, 2),
        "p95_ms": round(p95 * 1000, 2),
        "max_ms": round(max(durations) * 1000, 2),
    }
    (report_dir / "performance.json").write_text(json.dumps(payload, indent=2))
    assert p95 < 2.0
