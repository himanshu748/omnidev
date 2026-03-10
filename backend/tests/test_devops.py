import pytest

from app.schemas.devops import ParsedIntent
from app.routers import devops as devops_router
from app.services import devops_agent


@pytest.mark.asyncio
async def test_run_command_blocks_destructive(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(
            action="stop_ec2",
            params={"instance_ids": ["i-123"]},
            is_destructive=True,
        )

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    result = await devops_agent.run_command("Stop instance", confirm_destructive=False)
    assert result["needs_confirmation"] is True


@pytest.mark.asyncio
async def test_run_command_success(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(
            action="list_ec2",
            params={},
            is_destructive=False,
        )

    async def fake_dispatch(intent):
        return {"count": 0, "instances": []}

    async def fake_summarise(action, raw_result):
        return "No instances found"

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)
    result = await devops_agent.run_command("List instances")
    assert result["summary"] == "No instances found"
    assert result["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_devops_endpoint(client, monkeypatch, coverage_tracker):
    async def fake_run_command(message: str, confirm_destructive: bool = False):
        return {
            "action": "list_ec2",
            "params": {},
            "raw_result": {"count": 1},
            "summary": "Found 1 instance",
            "needs_confirmation": False,
        }

    monkeypatch.setattr(devops_router, "run_command", fake_run_command)
    resp = await client.post(
        "/api/devops/command",
        json={"message": "List instances", "confirm_destructive": False},
    )
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["action"] == "list_ec2"
    coverage_tracker("POST /api/devops/command")
