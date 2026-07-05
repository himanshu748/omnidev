import json

import boto3
import pytest
from moto import mock_aws

from app.config import settings
from app.schemas.devops import ParsedIntent
from app.routers import devops as devops_router
from app.services import devops_agent
from app.services.ai_service import AIConfigurationError


@pytest.fixture(autouse=True)
def _refill_bucket():
    """Keep the destructive token bucket full between tests."""
    devops_agent._refill_destructive_tokens()
    yield
    devops_agent._refill_destructive_tokens()


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
    plan = result["plan"]
    assert plan["service"] == "ec2"
    assert plan["operation"] == "stop_instances"
    assert plan["params"] == {"instance_ids": ["i-123"]}
    assert plan["destructive"] is True
    assert plan["read_only"] is False
    assert "impact" in plan


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
    plan = result["plan"]
    assert plan["service"] == "ec2"
    assert plan["operation"] == "describe_instances"
    assert plan["params"] == {}
    assert plan["destructive"] is False
    assert plan["read_only"] is True


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
async def test_plan_command_never_dispatches(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(
            action="terminate_ec2",
            params={"instance_ids": ["i-123"]},
            is_destructive=True,
        )

    async def fail_dispatch(intent):
        raise AssertionError("plan_command must never dispatch")

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fail_dispatch)
    result = await devops_agent.plan_command("Terminate instance i-123")
    assert result["plan"]["service"] == "ec2"
    assert result["plan"]["destructive"] is True
    assert "Nothing was executed" in result["summary"]


@pytest.mark.asyncio
async def test_plan_command_skips_read_only_execution(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="list_ec2", params={}, is_destructive=False)

    async def fail_dispatch(intent):
        raise AssertionError("plan_command must never dispatch, even read-only")

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fail_dispatch)
    result = await devops_agent.plan_command("List instances")
    assert result["plan"]["read_only"] is True


@pytest.mark.asyncio
async def test_plan_command_unsupported_has_no_plan(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="unsupported", params={}, is_destructive=False)

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    result = await devops_agent.plan_command("Make me a coffee")
    assert result["plan"] is None
    assert "not currently supported" in result["summary"]


@pytest.mark.asyncio
async def test_devops_plan_endpoint(client, monkeypatch, coverage_tracker):
    monkeypatch.setattr(settings, "gemini_api_key", "test-gemini-key")

    async def fake_plan_command(message: str):
        return {
            "action": "stop_ec2",
            "params": {"instance_ids": ["i-123"]},
            "plan": {"service": "ec2", "operation": "stop_instances", "destructive": True},
            "summary": "Plan preview for stop_ec2. Nothing was executed.",
        }

    monkeypatch.setattr(devops_router, "plan_command", fake_plan_command)
    resp = await client.post("/api/devops/plan", json={"message": "Stop instance i-123"})
    assert resp.status_code == 200
    payload = resp.json()
    assert payload["plan"]["destructive"] is True
    coverage_tracker("POST /api/devops/plan")


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


# ── Enriched plan ───────────────────────────────────────────
def test_build_plan_read_only_is_enriched():
    intent = ParsedIntent(action="list_ec2", params={"region": "eu-west-1"})
    plan = devops_agent.build_plan(intent)
    assert plan["service"] == "ec2"
    assert plan["operation"] == "describe_instances"
    assert plan["destructive"] is False
    assert plan["read_only"] is True
    assert "Read-only" in plan["impact"]
    assert plan["estimated_scope"]["region"] == "eu-west-1"


def test_build_plan_destructive_scope_counts_targets():
    intent = ParsedIntent(
        action="terminate_ec2",
        params={"instance_ids": ["i-1", "i-2", "i-3"]},
        is_destructive=True,
    )
    plan = devops_agent.build_plan(intent)
    assert plan["destructive"] is True
    assert plan["read_only"] is False
    assert "Irreversible" in plan["impact"]
    assert plan["estimated_scope"]["target_count"] == 3


def test_build_plan_new_readonly_action_maps():
    intent = ParsedIntent(action="get_caller_identity", params={})
    plan = devops_agent.build_plan(intent)
    assert plan["service"] == "sts"
    assert plan["operation"] == "get_caller_identity"
    assert plan["read_only"] is True


def test_new_actions_are_consistent():
    """Every new read-only action is wired everywhere and non-destructive."""
    new_actions = [
        "list_ecs_clusters",
        "list_ecs_services",
        "list_elb",
        "list_route53_zones",
        "list_cloudfront_distributions",
        "describe_s3_bucket",
        "list_sns_topics",
        "list_sqs_queues",
        "list_ecr_repositories",
        "get_caller_identity",
    ]
    for action in new_actions:
        assert action in devops_agent.SUPPORTED_ACTIONS
        assert action in devops_agent.ACTION_PLAN_MAP
        assert action in devops_agent.ACTION_IMPACT
        assert action not in devops_agent.DESTRUCTIVE_ACTIONS


# ── New read-only dispatch (moto) ───────────────────────────
@pytest.mark.asyncio
async def test_dispatch_get_caller_identity(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        intent = ParsedIntent(action="get_caller_identity", params={})
        result = await devops_agent._dispatch(intent)
        assert "account" in result
        assert "arn" in result
        assert "user_id" in result


@pytest.mark.asyncio
async def test_dispatch_list_sns_topics(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        sns = boto3.client("sns", region_name="us-east-1")
        sns.create_topic(Name="alerts")

        intent = ParsedIntent(action="list_sns_topics", params={})
        result = await devops_agent._dispatch(intent)
        assert result["count"] == 1
        assert result["topics"][0]["name"] == "alerts"


@pytest.mark.asyncio
async def test_dispatch_list_sqs_queues(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        sqs = boto3.client("sqs", region_name="us-east-1")
        sqs.create_queue(QueueName="jobs")

        intent = ParsedIntent(action="list_sqs_queues", params={})
        result = await devops_agent._dispatch(intent)
        assert result["count"] == 1
        assert result["queues"][0]["name"] == "jobs"


@pytest.mark.asyncio
async def test_dispatch_list_ecr_repositories(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        ecr = boto3.client("ecr", region_name="us-east-1")
        ecr.create_repository(repositoryName="my-app")

        intent = ParsedIntent(action="list_ecr_repositories", params={})
        result = await devops_agent._dispatch(intent)
        assert result["count"] == 1
        assert result["repositories"][0]["name"] == "my-app"


@pytest.mark.asyncio
async def test_dispatch_describe_s3_bucket(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="detail-bucket")
        s3.put_bucket_versioning(
            Bucket="detail-bucket",
            VersioningConfiguration={"Status": "Enabled"},
        )

        intent = ParsedIntent(
            action="describe_s3_bucket", params={"bucket": "detail-bucket"}
        )
        result = await devops_agent._dispatch(intent)
        assert result["bucket"] == "detail-bucket"
        assert result["versioning"] == "Enabled"
        assert "encrypted" in result


@pytest.mark.asyncio
async def test_dispatch_list_ecs_clusters(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        ecs = boto3.client("ecs", region_name="us-east-1")
        ecs.create_cluster(clusterName="prod")

        intent = ParsedIntent(action="list_ecs_clusters", params={})
        result = await devops_agent._dispatch(intent)
        assert result["count"] == 1
        assert result["clusters"][0]["name"] == "prod"


@pytest.mark.asyncio
async def test_run_command_readonly_new_action_end_to_end(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="get_caller_identity", params={})

    async def fake_dispatch(intent):
        return {"account": "123456789012", "arn": "arn:aws:iam::x:user/y", "user_id": "AIDA"}

    async def fake_summarise(action, raw_result):
        return "You are user y in account 123456789012."

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)
    result = await devops_agent.run_command("Who am I")
    assert result["needs_confirmation"] is False
    assert result["plan"]["read_only"] is True
    assert result["plan"]["service"] == "sts"
    assert result["raw_result"]["account"] == "123456789012"


# ── Destructive throttle ────────────────────────────────────
@pytest.mark.asyncio
async def test_destructive_throttle_refuses_when_exhausted(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(
            action="stop_ec2",
            params={"instance_ids": ["i-1"]},
            is_destructive=True,
        )

    dispatched = {"count": 0}

    async def fake_dispatch(intent):
        dispatched["count"] += 1
        return {"stopped": True}

    async def fake_summarise(action, raw_result):
        return "stopped"

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)

    # Drain the whole bucket via confirmed destructive calls.
    for _ in range(devops_agent._DESTRUCTIVE_BUCKET_CAPACITY):
        res = await devops_agent.run_command("Stop it", confirm_destructive=True)
        assert res["needs_confirmation"] is False

    # Next one must be refused without dispatching.
    before = dispatched["count"]
    blocked = await devops_agent.run_command("Stop it", confirm_destructive=True)
    assert "rate limit" in blocked["summary"].lower()
    assert blocked["raw_result"] is None
    assert dispatched["count"] == before


@pytest.mark.asyncio
async def test_destructive_throttle_does_not_touch_readonly(monkeypatch):
    async def fake_parse(message: str):
        return ParsedIntent(action="list_ec2", params={}, is_destructive=False)

    async def fake_dispatch(intent):
        return {"count": 0, "instances": []}

    async def fake_summarise(action, raw_result):
        return "none"

    monkeypatch.setattr(devops_agent, "parse_intent", fake_parse)
    monkeypatch.setattr(devops_agent, "_dispatch", fake_dispatch)
    monkeypatch.setattr(devops_agent, "summarise", fake_summarise)

    # Drain the destructive bucket manually; read-only must still pass.
    for _ in range(devops_agent._DESTRUCTIVE_BUCKET_CAPACITY + 5):
        devops_agent._consume_destructive_token()

    result = await devops_agent.run_command("List instances")
    assert result["needs_confirmation"] is False
    assert result["raw_result"]["count"] == 0
