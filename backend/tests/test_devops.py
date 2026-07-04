import json

import pytest

from app.config import settings
from app.schemas.devops import ParsedIntent
from app.routers import devops as devops_router
from app.services import devops_agent
from app.services.ai_service import AIConfigurationError


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
    assert result["plan"] == {
        "service": "ec2",
        "operation": "stop_instances",
        "params": {"instance_ids": ["i-123"]},
        "destructive": True,
    }


@pytest.mark.asyncio
async def test_run_command_blocks_registry_destructive_when_model_misses_it(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(
            action="create_s3_bucket",
            params={"bucket_name": "demo", "region": "us-east-1"},
            is_destructive=False,
        )

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    result = await devops_agent.run_command("Create an S3 bucket", confirm_destructive=False)
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
    assert result["plan"] == {
        "service": "ec2",
        "operation": "describe_instances",
        "params": {},
        "destructive": False,
    }


@pytest.mark.asyncio
async def test_run_command_unsupported_has_no_plan(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="unsupported", params={}, is_destructive=False)

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    result = await devops_agent.run_command("Make me a coffee")
    assert result["needs_confirmation"] is False
    assert result["plan"] is None


@pytest.mark.asyncio
async def test_run_command_read_only_refuses_destructive(monkeypatch):
    monkeypatch.setattr(settings, "devops_read_only", True)

    async def fake_parse(message: str):
        return ParsedIntent(
            action="terminate_ec2",
            params={"instance_ids": ["i-123"]},
            is_destructive=True,
        )

    async def fail_dispatch(intent):
        raise AssertionError("dispatch must not run in read-only mode")

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fail_dispatch)
    result = await devops_agent.run_command("Terminate instance", confirm_destructive=True)
    assert result["needs_confirmation"] is False
    assert result["raw_result"] is None
    assert "read-only mode (DEVOPS_READ_ONLY=1)" in result["summary"]
    assert result["plan"]["destructive"] is True


@pytest.mark.asyncio
async def test_run_command_writes_audit_line(monkeypatch, tmp_path):
    audit_path = tmp_path / "audit.jsonl"
    monkeypatch.setattr(settings, "audit_log_path", str(audit_path))

    async def fake_parse(message: str):
        return ParsedIntent(action="list_ec2", params={}, is_destructive=False)

    async def fake_dispatch(intent):
        return {"count": 0, "instances": []}

    async def fake_summarise(action, raw_result):
        return "No instances found"

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)
    await devops_agent.run_command("List instances")

    lines = audit_path.read_text().strip().splitlines()
    assert len(lines) == 1
    entry = json.loads(lines[0])
    assert entry["action"] == "list_ec2"
    assert entry["destructive"] is False
    assert entry["ok"] is True
    assert entry["error"] is None
    assert entry["ts"]


@pytest.mark.asyncio
async def test_run_command_audit_failure_does_not_break_request(monkeypatch, tmp_path):
    monkeypatch.setattr(settings, "audit_log_path", str(tmp_path / "no-such-dir" / "audit.jsonl"))

    async def fake_parse(message: str):
        return ParsedIntent(action="list_ec2", params={}, is_destructive=False)

    async def fake_dispatch(intent):
        return {"count": 0, "instances": []}

    async def fake_summarise(action, raw_result):
        return "No instances found"

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)
    result = await devops_agent.run_command("List instances")
    assert result["summary"] == "No instances found"


@pytest.mark.asyncio
async def test_run_command_summarise_failure_falls_back(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="list_ec2", params={}, is_destructive=False)

    async def fake_dispatch(intent):
        return {"count": 2, "instances": [{"id": "i-1"}, {"id": "i-2"}]}

    async def broken_summarise(action, raw_result):
        raise RuntimeError("model exploded")

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", broken_summarise)
    result = await devops_agent.run_command("List instances")
    assert result["summary"] == "Action list_ec2 completed. See raw result."
    assert result["raw_result"]["count"] == 2
    assert result["needs_confirmation"] is False


@pytest.mark.asyncio
async def test_devops_endpoint(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")
    monkeypatch.setattr(settings, "aws_access_key_id", "test-access-key")
    monkeypatch.setattr(settings, "aws_secret_access_key", "test-secret-key")

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


@pytest.mark.asyncio
async def test_devops_endpoint_returns_503_without_gemini_key(client, monkeypatch):
    monkeypatch.setattr(settings, "ai_provider", "gemini")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "aws_access_key_id", "test-access-key")
    monkeypatch.setattr(settings, "aws_secret_access_key", "test-secret-key")

    resp = await client.post(
        "/api/devops/command",
        json={"message": "List instances", "confirm_destructive": False},
    )

    assert resp.status_code == 503
    assert "GEMINI_API_KEY" in resp.json()["detail"]


@pytest.mark.asyncio
async def test_devops_endpoint_returns_503_when_ollama_unreachable(client, monkeypatch):
    async def fake_run_command(message: str, confirm_destructive: bool = False):
        raise AIConfigurationError("Cannot reach Ollama at http://localhost:11434.")

    monkeypatch.setattr(devops_router, "run_command", fake_run_command)

    resp = await client.post(
        "/api/devops/command",
        json={"message": "List instances", "confirm_destructive": False},
    )

    assert resp.status_code == 503
    assert "Ollama" in resp.json()["detail"]
