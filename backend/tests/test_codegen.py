import pytest

from app.routers import codegen as codegen_router


@pytest.mark.asyncio
async def test_codegen_endpoint(client, monkeypatch, coverage_tracker):
    async def fake_generate_project(prompt: str, framework: str):
        return {
            "files": [{"path": "app.py", "content": "print('ok')"}],
            "instructions": "run app.py",
        }

    monkeypatch.setattr(codegen_router, "generate_project", fake_generate_project)
    resp = await client.post(
        "/api/codegen/generate",
        json={"prompt": "Build a tool", "framework": "python"},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["files"][0]["path"] == "app.py"
    coverage_tracker("POST /api/codegen/generate")
