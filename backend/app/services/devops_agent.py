"""
DevOps Agent service — v3 (Gemini).
1. Parse natural-language command via Gemini -> structured intent
2. Dispatch to the matching boto3 AWS call
3. Summarise the result with Gemini

Supported AWS services: EC2, S3, VPC, IAM, RDS, CloudWatch, Lambda.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

import boto3
from google.genai import types

from app.config import settings
from app.schemas.devops import ParsedIntent
from app.services.ai_service import (
    extract_function_call,
    generate_text,
    generate_with_tool,
)

# ── Supported actions ───────────────────────────────────────
SUPPORTED_ACTIONS = [
    "list_ec2",
    "describe_ec2_instance",
    "launch_ec2",
    "stop_ec2",
    "terminate_ec2",
    "reboot_ec2",
    "list_s3_buckets",
    "list_s3_objects",
    "create_s3_bucket",
    "describe_security_groups",
    "list_vpcs",
    "list_iam_users",
    "describe_rds_instances",
    "list_cloudwatch_alarms",
    "list_lambda_functions",
]

DESTRUCTIVE_ACTIONS = {
    "stop_ec2",
    "terminate_ec2",
    "reboot_ec2",
    "launch_ec2",
    "create_s3_bucket",
}

SYSTEM_PROMPT = f"""\
You are an AWS DevOps assistant. The user gives you a natural-language command
about AWS resources. Your job is to extract a structured intent.

Return the extracted intent by calling the return_intent tool.

Supported actions: {SUPPORTED_ACTIONS}

EC2:
- list_ec2              -> {{}}  (optional "filters", "region")
- describe_ec2_instance -> {{"instance_id": "i-..."}}
- launch_ec2            -> {{"image_id": "ami-...", "instance_type": "t2.micro", "count": 1}}  (destructive)
- stop_ec2              -> {{"instance_ids": ["i-..."]}}  (destructive)
- terminate_ec2         -> {{"instance_ids": ["i-..."]}}  (destructive)
- reboot_ec2            -> {{"instance_ids": ["i-..."]}}  (destructive)

S3:
- list_s3_buckets       -> {{}}
- list_s3_objects        -> {{"bucket": "my-bucket", "prefix": "", "max_keys": 100}}
- create_s3_bucket      -> {{"bucket_name": "new-bucket", "region": "us-east-1"}}  (destructive)

Networking:
- describe_security_groups -> {{}}  (optional "group_ids")
- list_vpcs             -> {{}}  (optional "vpc_ids")

IAM:
- list_iam_users        -> {{}}  (optional "path_prefix")

RDS:
- describe_rds_instances -> {{}}  (optional "db_instance_id")

CloudWatch:
- list_cloudwatch_alarms -> {{}}  (optional "alarm_names", "state")

Lambda:
- list_lambda_functions  -> {{}}

If the user's request doesn't map to a supported action, use action="unsupported".
"""

INTENT_TOOL = types.FunctionDeclaration(
    name="return_intent",
    description="Extract a supported AWS action, params, and destructive flag from the user's request.",
    parameters=types.Schema(
        type="OBJECT",
        properties={
            "action": types.Schema(
                type="STRING",
                description="The AWS action to perform",
                enum=[*SUPPORTED_ACTIONS, "unsupported"],
            ),
            "params": types.Schema(
                type="OBJECT",
                description="Parameters for the action as key-value pairs",
            ),
            "is_destructive": types.Schema(
                type="BOOLEAN",
                description="Whether the action is destructive",
            ),
        },
        required=["action", "params", "is_destructive"],
    ),
)


# ── Intent parsing ──────────────────────────────────────────
async def parse_intent(message: str) -> ParsedIntent:
    resp = await generate_with_tool(
        message,
        system=SYSTEM_PROMPT,
        tools=[INTENT_TOOL],
        forced_function="return_intent",
        max_tokens=1024,
    )
    data = extract_function_call(resp, "return_intent")
    return ParsedIntent(**data)


# ── boto3 clients ───────────────────────────────────────────
def _aws_client_kwargs() -> dict[str, str]:
    if settings.aws_access_key_id and settings.aws_secret_access_key:
        return {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
        }
    return {}


def _ec2_client(region: str | None = None):
    return boto3.client(
        "ec2",
        region_name=region or settings.aws_default_region,
        **_aws_client_kwargs(),
    )


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_default_region,
        **_aws_client_kwargs(),
    )


def _iam_client():
    return boto3.client(
        "iam",
        **_aws_client_kwargs(),
    )


def _rds_client(region: str | None = None):
    return boto3.client(
        "rds",
        region_name=region or settings.aws_default_region,
        **_aws_client_kwargs(),
    )


def _cloudwatch_client(region: str | None = None):
    return boto3.client(
        "cloudwatch",
        region_name=region or settings.aws_default_region,
        **_aws_client_kwargs(),
    )


def _lambda_client(region: str | None = None):
    return boto3.client(
        "lambda",
        region_name=region or settings.aws_default_region,
        **_aws_client_kwargs(),
    )


# ── boto3 dispatch ──────────────────────────────────────────
async def _dispatch(intent: ParsedIntent) -> Any:
    """Run the matching boto3 call in a thread (boto3 is sync)."""
    action = intent.action
    params = intent.params

    def _run() -> Any:
        if action == "list_ec2":
            ec2 = _ec2_client(params.get("region"))
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
                            "private_ip": inst.get("PrivateIpAddress", ""),
                            "vpc_id": inst.get("VpcId", ""),
                            "subnet_id": inst.get("SubnetId", ""),
                            "az": inst.get("Placement", {}).get("AvailabilityZone", ""),
                        }
                    )
            return {"count": len(instances), "instances": instances}

        if action == "describe_ec2_instance":
            ec2 = _ec2_client(params.get("region"))
            instance_id = params["instance_id"]
            resp = ec2.describe_instances(InstanceIds=[instance_id])
            inst = resp["Reservations"][0]["Instances"][0]
            name = ""
            tags = {}
            for tag in inst.get("Tags", []):
                tags[tag["Key"]] = tag["Value"]
                if tag["Key"] == "Name":
                    name = tag["Value"]
            sgs = [
                {"id": sg["GroupId"], "name": sg["GroupName"]}
                for sg in inst.get("SecurityGroups", [])
            ]
            return {
                "id": inst["InstanceId"],
                "type": inst["InstanceType"],
                "state": inst["State"]["Name"],
                "name": name,
                "image_id": inst.get("ImageId", ""),
                "key_name": inst.get("KeyName", ""),
                "launch_time": str(inst.get("LaunchTime", "")),
                "public_ip": inst.get("PublicIpAddress", ""),
                "private_ip": inst.get("PrivateIpAddress", ""),
                "vpc_id": inst.get("VpcId", ""),
                "subnet_id": inst.get("SubnetId", ""),
                "az": inst.get("Placement", {}).get("AvailabilityZone", ""),
                "security_groups": sgs,
                "tags": tags,
                "platform": inst.get("PlatformDetails", ""),
                "architecture": inst.get("Architecture", ""),
            }

        if action == "launch_ec2":
            ec2 = _ec2_client(params.get("region"))
            resp = ec2.run_instances(
                ImageId=params.get("image_id", "ami-0c02fb55956c7d316"),
                InstanceType=params.get("instance_type", "t2.micro"),
                MinCount=params.get("count", 1),
                MaxCount=params.get("count", 1),
            )
            ids = [i["InstanceId"] for i in resp["Instances"]]
            return {"launched_instance_ids": ids}

        if action == "stop_ec2":
            ec2 = _ec2_client(params.get("region"))
            resp = ec2.stop_instances(InstanceIds=params["instance_ids"])
            return resp["StoppingInstances"]

        if action == "terminate_ec2":
            ec2 = _ec2_client(params.get("region"))
            resp = ec2.terminate_instances(InstanceIds=params["instance_ids"])
            return resp["TerminatingInstances"]

        if action == "reboot_ec2":
            ec2 = _ec2_client(params.get("region"))
            ec2.reboot_instances(InstanceIds=params["instance_ids"])
            return {"rebooted_instance_ids": params["instance_ids"]}

        if action == "list_s3_buckets":
            s3 = _s3_client()
            resp = s3.list_buckets()
            buckets = [
                {"name": b["Name"], "created": str(b["CreationDate"])}
                for b in resp.get("Buckets", [])
            ]
            return {"count": len(buckets), "buckets": buckets}

        if action == "list_s3_objects":
            s3 = _s3_client()
            bucket = params["bucket"]
            prefix = params.get("prefix", "")
            max_keys = params.get("max_keys", 100)
            resp = s3.list_objects_v2(
                Bucket=bucket, Prefix=prefix, MaxKeys=max_keys
            )
            objects = [
                {
                    "key": obj["Key"],
                    "size_bytes": obj["Size"],
                    "last_modified": str(obj["LastModified"]),
                    "storage_class": obj.get("StorageClass", ""),
                }
                for obj in resp.get("Contents", [])
            ]
            return {
                "bucket": bucket,
                "prefix": prefix,
                "count": len(objects),
                "is_truncated": resp.get("IsTruncated", False),
                "objects": objects,
            }

        if action == "create_s3_bucket":
            s3 = _s3_client()
            bucket_name = params["bucket_name"]
            region = params.get("region", settings.aws_default_region)
            if region == "us-east-1":
                s3.create_bucket(Bucket=bucket_name)
            else:
                s3.create_bucket(
                    Bucket=bucket_name,
                    CreateBucketConfiguration={"LocationConstraint": region},
                )
            return {"created_bucket": bucket_name, "region": region}

        if action == "describe_security_groups":
            ec2 = _ec2_client(params.get("region"))
            kwargs = {}
            if params.get("group_ids"):
                kwargs["GroupIds"] = params["group_ids"]
            resp = ec2.describe_security_groups(**kwargs)
            sgs = []
            for sg in resp.get("SecurityGroups", []):
                ingress_rules = [
                    {
                        "protocol": r.get("IpProtocol", ""),
                        "from_port": r.get("FromPort", ""),
                        "to_port": r.get("ToPort", ""),
                        "sources": [
                            ip.get("CidrIp", "") for ip in r.get("IpRanges", [])
                        ],
                    }
                    for r in sg.get("IpPermissions", [])
                ]
                sgs.append(
                    {
                        "id": sg["GroupId"],
                        "name": sg["GroupName"],
                        "description": sg["Description"],
                        "vpc_id": sg.get("VpcId", ""),
                        "ingress_rules_count": len(ingress_rules),
                        "ingress_rules": ingress_rules[:10],
                    }
                )
            return {"count": len(sgs), "security_groups": sgs}

        if action == "list_vpcs":
            ec2 = _ec2_client(params.get("region"))
            kwargs = {}
            if params.get("vpc_ids"):
                kwargs["VpcIds"] = params["vpc_ids"]
            resp = ec2.describe_vpcs(**kwargs)
            vpcs = []
            for vpc in resp.get("Vpcs", []):
                name = ""
                for tag in vpc.get("Tags", []):
                    if tag["Key"] == "Name":
                        name = tag["Value"]
                vpcs.append(
                    {
                        "id": vpc["VpcId"],
                        "name": name,
                        "cidr": vpc["CidrBlock"],
                        "state": vpc["State"],
                        "is_default": vpc.get("IsDefault", False),
                    }
                )
            return {"count": len(vpcs), "vpcs": vpcs}

        if action == "list_iam_users":
            iam = _iam_client()
            path = params.get("path_prefix", "/")
            resp = iam.list_users(PathPrefix=path)
            users = []
            for u in resp.get("Users", []):
                users.append(
                    {
                        "username": u["UserName"],
                        "user_id": u["UserId"],
                        "arn": u["Arn"],
                        "created": str(u.get("CreateDate", "")),
                        "password_last_used": str(u.get("PasswordLastUsed", "")),
                    }
                )
            return {"count": len(users), "users": users}

        if action == "describe_rds_instances":
            rds = _rds_client(params.get("region"))
            kwargs = {}
            if params.get("db_instance_id"):
                kwargs["DBInstanceIdentifier"] = params["db_instance_id"]
            resp = rds.describe_db_instances(**kwargs)
            databases = []
            for db in resp.get("DBInstances", []):
                databases.append(
                    {
                        "id": db["DBInstanceIdentifier"],
                        "engine": db["Engine"],
                        "engine_version": db.get("EngineVersion", ""),
                        "class": db["DBInstanceClass"],
                        "status": db["DBInstanceStatus"],
                        "storage_gb": db.get("AllocatedStorage", 0),
                        "endpoint": db.get("Endpoint", {}).get("Address", ""),
                        "port": db.get("Endpoint", {}).get("Port", ""),
                        "multi_az": db.get("MultiAZ", False),
                        "vpc_id": db.get("DBSubnetGroup", {}).get("VpcId", ""),
                    }
                )
            return {"count": len(databases), "databases": databases}

        if action == "list_cloudwatch_alarms":
            cw = _cloudwatch_client(params.get("region"))
            kwargs = {}
            if params.get("alarm_names"):
                kwargs["AlarmNames"] = params["alarm_names"]
            if params.get("state"):
                kwargs["StateValue"] = params["state"]
            resp = cw.describe_alarms(**kwargs)
            alarms = []
            for a in resp.get("MetricAlarms", []):
                alarms.append(
                    {
                        "name": a["AlarmName"],
                        "state": a["StateValue"],
                        "metric": a.get("MetricName", ""),
                        "namespace": a.get("Namespace", ""),
                        "comparison": a.get("ComparisonOperator", ""),
                        "threshold": a.get("Threshold", 0),
                        "period_seconds": a.get("Period", 0),
                        "description": a.get("AlarmDescription", ""),
                        "last_updated": str(a.get("StateUpdatedTimestamp", "")),
                    }
                )
            return {"count": len(alarms), "alarms": alarms}

        if action == "list_lambda_functions":
            lam = _lambda_client(params.get("region"))
            resp = lam.list_functions()
            functions = []
            for f in resp.get("Functions", []):
                functions.append(
                    {
                        "name": f["FunctionName"],
                        "runtime": f.get("Runtime", ""),
                        "handler": f.get("Handler", ""),
                        "code_size_bytes": f.get("CodeSize", 0),
                        "memory_mb": f.get("MemorySize", 0),
                        "timeout_seconds": f.get("Timeout", 0),
                        "last_modified": f.get("LastModified", ""),
                        "description": f.get("Description", ""),
                        "arn": f["FunctionArn"],
                    }
                )
            return {"count": len(functions), "functions": functions}

        return {"error": f"Unsupported action: {action}"}

    return await asyncio.to_thread(_run)


# ── Summarise ───────────────────────────────────────────────
async def summarise(action: str, raw_result: Any) -> str:
    return await generate_text(
        f"Action: {action}\nResult:\n{json.dumps(raw_result, default=str)}",
        system=(
            "You are a DevOps expert. Summarise the following AWS API result "
            "in a clear, concise, human-friendly way. Include counts, key data, "
            "and any noteworthy details. Use plain text, no markdown."
        ),
        temperature=0.3,
        max_tokens=512,
    )


# ── Public orchestrator ─────────────────────────────────────
async def run_command(message: str, confirm_destructive: bool = False) -> dict:
    intent = await parse_intent(message)

    if intent.action == "unsupported":
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": (
                "Sorry, that action is not currently supported. "
                "Supported services: EC2, S3, VPC, IAM, RDS, CloudWatch, Lambda."
            ),
            "needs_confirmation": False,
        }

    is_destructive = intent.action in DESTRUCTIVE_ACTIONS or intent.is_destructive

    if is_destructive and not confirm_destructive:
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": f"This is a destructive action ({intent.action}). "
            "Please enable 'Confirm destructive actions' and try again.",
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
