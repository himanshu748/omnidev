"""
DevOps Agent service.
1. Parse natural-language command via OpenAI → structured intent
2. Dispatch to the matching boto3 AWS call
3. Summarise the result with OpenAI
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from openai import AsyncOpenAI

from app.config import settings
from app.schemas.devops import ParsedIntent

# ── OpenAI client ───────────────────────────────────────────
_openai = AsyncOpenAI(api_key=settings.openai_api_key)

# ── Supported actions ───────────────────────────────────────
SUPPORTED_ACTIONS = [
    "list_ec2",
    "launch_ec2",
    "stop_ec2",
    "terminate_ec2",
    "list_s3_buckets",
    "describe_security_groups",
]

DESTRUCTIVE_ACTIONS = {"stop_ec2", "terminate_ec2"}

SYSTEM_PROMPT = f"""\
You are an AWS DevOps assistant. The user gives you a natural-language command
about AWS resources. Your job is to extract a structured intent.

Respond ONLY with a JSON object — no markdown, no explanation:
{{
  "action": "<one of {SUPPORTED_ACTIONS}>",
  "params": {{...}},          // relevant parameters
  "is_destructive": true/false
}}

Supported actions and expected params:
- list_ec2              → {{}}  (optional "filters": [{{"Name":"...", "Values":["..."]}}])
- launch_ec2            → {{"image_id": "ami-...", "instance_type": "t2.micro", "count": 1}}
- stop_ec2              → {{"instance_ids": ["i-..."]}}
- terminate_ec2         → {{"instance_ids": ["i-..."]}}
- list_s3_buckets       → {{}}
- describe_security_groups → {{}}  (optional "group_ids": ["sg-..."])

If the user's request doesn't map to a supported action, respond with:
{{"action": "unsupported", "params": {{}}, "is_destructive": false}}
"""


# ── Intent parsing ──────────────────────────────────────────
async def parse_intent(message: str) -> ParsedIntent:
    resp = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": message},
        ],
        temperature=0,
        response_format={"type": "json_object"},
    )
    raw = resp.choices[0].message.content or "{}"
    data = json.loads(raw)
    return ParsedIntent(**data)


# ── boto3 dispatch ──────────────────────────────────────────
def _ec2_client():
    return boto3.client(
        "ec2",
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


async def _dispatch(intent: ParsedIntent) -> Any:
    """Run the matching boto3 call in a thread (boto3 is sync)."""
    action = intent.action
    params = intent.params

    def _run() -> Any:
        if action == "list_ec2":
            ec2 = _ec2_client()
            filters = params.get("filters", [])
            kwargs = {"Filters": filters} if filters else {}
            resp = ec2.describe_instances(**kwargs)
            instances = []
            for reservation in resp.get("Reservations", []):
                for inst in reservation.get("Instances", []):
                    name = ""
                    for tag in inst.get("Tags", []):
                        if tag["Key"] == "Name":
                            name = tag["Value"]
                    instances.append(
                        {
                            "id": inst["InstanceId"],
                            "type": inst["InstanceType"],
                            "state": inst["State"]["Name"],
                            "name": name,
                            "launch_time": str(inst.get("LaunchTime", "")),
                            "public_ip": inst.get("PublicIpAddress", ""),
                        }
                    )
            return instances

        if action == "launch_ec2":
            ec2 = _ec2_client()
            resp = ec2.run_instances(
                ImageId=params.get("image_id", "ami-0c02fb55956c7d316"),
                InstanceType=params.get("instance_type", "t2.micro"),
                MinCount=params.get("count", 1),
                MaxCount=params.get("count", 1),
            )
            ids = [i["InstanceId"] for i in resp["Instances"]]
            return {"launched_instance_ids": ids}

        if action == "stop_ec2":
            ec2 = _ec2_client()
            resp = ec2.stop_instances(InstanceIds=params["instance_ids"])
            return resp["StoppingInstances"]

        if action == "terminate_ec2":
            ec2 = _ec2_client()
            resp = ec2.terminate_instances(InstanceIds=params["instance_ids"])
            return resp["TerminatingInstances"]

        if action == "list_s3_buckets":
            s3 = _s3_client()
            resp = s3.list_buckets()
            return [
                {"name": b["Name"], "created": str(b["CreationDate"])}
                for b in resp.get("Buckets", [])
            ]

        if action == "describe_security_groups":
            ec2 = _ec2_client()
            kwargs = {}
            if params.get("group_ids"):
                kwargs["GroupIds"] = params["group_ids"]
            resp = ec2.describe_security_groups(**kwargs)
            return [
                {
                    "id": sg["GroupId"],
                    "name": sg["GroupName"],
                    "description": sg["Description"],
                    "vpc_id": sg.get("VpcId", ""),
                }
                for sg in resp.get("SecurityGroups", [])
            ]

        return {"error": f"Unsupported action: {action}"}

    return await asyncio.to_thread(_run)


# ── Summarise ───────────────────────────────────────────────
async def summarise(action: str, raw_result: Any) -> str:
    resp = await _openai.chat.completions.create(
        model=settings.openai_model,
        messages=[
            {
                "role": "system",
                "content": "Summarise the following AWS API result in a clear, concise, human-friendly way.",
            },
            {
                "role": "user",
                "content": f"Action: {action}\nResult:\n{json.dumps(raw_result, default=str)}",
            },
        ],
        temperature=0.3,
        max_tokens=512,
    )
    return resp.choices[0].message.content or ""


# ── Public orchestrator ─────────────────────────────────────
async def run_command(message: str, confirm_destructive: bool = False) -> dict:
    intent = await parse_intent(message)

    if intent.action == "unsupported":
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": "Sorry, that action is not supported yet.",
            "needs_confirmation": False,
        }

    # Safety gate for destructive actions
    if intent.is_destructive and not confirm_destructive:
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": f"This is a destructive action ({intent.action}). "
            "Please resend with confirm_destructive=true to proceed.",
            "needs_confirmation": True,
        }

    try:
        raw_result = await _dispatch(intent)
    except Exception as exc:
        error_msg = str(exc)
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": {"error": error_msg},
            "summary": f"AWS call failed: {error_msg}",
            "needs_confirmation": False,
        }

    summary = await summarise(intent.action, raw_result)

    return {
        "action": intent.action,
        "params": intent.params,
        "raw_result": raw_result,
        "summary": summary,
        "needs_confirmation": False,
    }
