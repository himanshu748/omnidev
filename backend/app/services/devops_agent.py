"""
DevOps Agent service.
1. Parse natural-language command via the AI provider -> structured intent
2. Dispatch to the matching boto3 AWS call
3. Summarise the result with the AI provider

Works with Gemini (cloud) or Ollama (local/offline) via ai_service.
Supported AWS services: EC2, S3, VPC, IAM, RDS, CloudWatch, Lambda,
ECS, ELBv2, Route53, CloudFront, SNS, SQS, ECR, STS.
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any

import boto3

logger = logging.getLogger(__name__)

from app.config import settings
from app.schemas.devops import ParsedIntent
from app.services.ai_service import generate_structured, generate_text

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
    # ── New read-only actions ──
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

DESTRUCTIVE_ACTIONS = {
    "stop_ec2",
    "terminate_ec2",
    "reboot_ec2",
    "launch_ec2",
    "create_s3_bucket",
}

# Human-readable, coarse impact strings per action for the enriched plan.
# Read-only actions are safe; destructive ones spell out what changes.
ACTION_IMPACT: dict[str, str] = {
    "list_ec2": "Read-only: lists EC2 instances. No changes.",
    "describe_ec2_instance": "Read-only: reads one EC2 instance. No changes.",
    "launch_ec2": "Creates and starts a new EC2 instance (incurs cost).",
    "stop_ec2": "Stops running EC2 instance(s); they can be started again.",
    "terminate_ec2": "Permanently terminates EC2 instance(s). Irreversible.",
    "reboot_ec2": "Reboots EC2 instance(s); brief downtime.",
    "list_s3_buckets": "Read-only: lists S3 buckets. No changes.",
    "list_s3_objects": "Read-only: lists objects in an S3 bucket. No changes.",
    "create_s3_bucket": "Creates a new S3 bucket in the account.",
    "describe_security_groups": "Read-only: reads security groups. No changes.",
    "list_vpcs": "Read-only: lists VPCs. No changes.",
    "list_iam_users": "Read-only: lists IAM users. No changes.",
    "describe_rds_instances": "Read-only: reads RDS instances. No changes.",
    "list_cloudwatch_alarms": "Read-only: lists CloudWatch alarms. No changes.",
    "list_lambda_functions": "Read-only: lists Lambda functions. No changes.",
    "list_ecs_clusters": "Read-only: lists ECS clusters. No changes.",
    "list_ecs_services": "Read-only: lists ECS services in a cluster. No changes.",
    "list_elb": "Read-only: lists load balancers and target health. No changes.",
    "list_route53_zones": "Read-only: lists Route53 hosted zones. No changes.",
    "list_cloudfront_distributions": "Read-only: lists CloudFront distributions. No changes.",
    "describe_s3_bucket": "Read-only: reads one S3 bucket's config. No changes.",
    "list_sns_topics": "Read-only: lists SNS topics. No changes.",
    "list_sqs_queues": "Read-only: lists SQS queues. No changes.",
    "list_ecr_repositories": "Read-only: lists ECR repositories. No changes.",
    "get_caller_identity": "Read-only: returns the calling AWS identity. No changes.",
}

# ── Plan mapping: action -> (aws service, boto3 operation) ──
ACTION_PLAN_MAP: dict[str, tuple[str, str]] = {
    "list_ec2": ("ec2", "describe_instances"),
    "describe_ec2_instance": ("ec2", "describe_instances"),
    "launch_ec2": ("ec2", "run_instances"),
    "stop_ec2": ("ec2", "stop_instances"),
    "terminate_ec2": ("ec2", "terminate_instances"),
    "reboot_ec2": ("ec2", "reboot_instances"),
    "list_s3_buckets": ("s3", "list_buckets"),
    "list_s3_objects": ("s3", "list_objects_v2"),
    "create_s3_bucket": ("s3", "create_bucket"),
    "describe_security_groups": ("ec2", "describe_security_groups"),
    "list_vpcs": ("ec2", "describe_vpcs"),
    "list_iam_users": ("iam", "list_users"),
    "describe_rds_instances": ("rds", "describe_db_instances"),
    "list_cloudwatch_alarms": ("cloudwatch", "describe_alarms"),
    "list_lambda_functions": ("lambda", "list_functions"),
    "list_ecs_clusters": ("ecs", "list_clusters"),
    "list_ecs_services": ("ecs", "list_services"),
    "list_elb": ("elbv2", "describe_load_balancers"),
    "list_route53_zones": ("route53", "list_hosted_zones"),
    "list_cloudfront_distributions": ("cloudfront", "list_distributions"),
    "describe_s3_bucket": ("s3", "get_bucket_encryption"),
    "list_sns_topics": ("sns", "list_topics"),
    "list_sqs_queues": ("sqs", "list_queues"),
    "list_ecr_repositories": ("ecr", "describe_repositories"),
    "get_caller_identity": ("sts", "get_caller_identity"),
}


def _estimated_scope(intent: ParsedIntent, service: str) -> dict[str, Any]:
    """Best-effort, trivially-known scope hints for the plan preview.

    Purely derived from the intent params — never calls AWS. Keeps the
    plan cheap and deterministic. Only include keys we actually know.
    """
    params = intent.params
    scope: dict[str, Any] = {}

    # Region: explicit param, else the default (global services have none).
    if service in ("iam", "s3", "route53", "cloudfront", "sts"):
        # Global or region-agnostic control planes.
        scope["region"] = params.get("region") or "global"
    else:
        scope["region"] = params.get("region") or settings.aws_default_region

    # Count target when the action names specific resources.
    for key in ("instance_ids", "group_ids", "vpc_ids", "alarm_names"):
        val = params.get(key)
        if isinstance(val, list):
            scope["target_count"] = len(val)
            break

    # Named single-resource targets.
    for key in ("instance_id", "bucket", "bucket_name", "db_instance_id", "cluster"):
        if params.get(key):
            scope["target"] = params[key]
            break

    return scope


def build_plan(intent: ParsedIntent) -> dict[str, Any] | None:
    """Preview of the boto3 call an intent would trigger, before execution.

    The dict is additive/backward-compatible: it always carries the original
    service/operation/params/destructive keys, plus the enriched read_only,
    impact, and estimated_scope keys.
    """
    mapping = ACTION_PLAN_MAP.get(intent.action)
    if mapping is None:
        return None
    service, operation = mapping
    destructive = intent.action in DESTRUCTIVE_ACTIONS or intent.is_destructive
    return {
        "service": service,
        "operation": operation,
        "params": intent.params,
        "destructive": destructive,
        "read_only": not destructive,
        "impact": ACTION_IMPACT.get(
            intent.action,
            "Destructive: modifies AWS resources."
            if destructive
            else "Read-only: no changes.",
        ),
        "estimated_scope": _estimated_scope(intent, service),
    }


# ── Destructive-action throttle (in-process token bucket) ───
# A tiny deterministic guard so a runaway loop can't fire an unbounded
# number of destructive AWS calls. No wall-clock: tokens are consumed per
# call and only refilled explicitly (e.g. by tests). Module-level + locked
# so it is shared across requests in one process.
_DESTRUCTIVE_BUCKET_CAPACITY = int(os.getenv("DEVOPS_DESTRUCTIVE_BUCKET", "10"))
_destructive_tokens = _DESTRUCTIVE_BUCKET_CAPACITY
_destructive_lock = threading.Lock()


def _consume_destructive_token() -> bool:
    """Take one token for a destructive action. False when exhausted."""
    global _destructive_tokens
    with _destructive_lock:
        if _destructive_tokens <= 0:
            return False
        _destructive_tokens -= 1
        return True


def _refill_destructive_tokens() -> None:
    """Reset the destructive bucket to capacity (used by tests/ops)."""
    global _destructive_tokens
    with _destructive_lock:
        _destructive_tokens = _DESTRUCTIVE_BUCKET_CAPACITY


# ── Audit log ───────────────────────────────────────────────
def _audit_log(action: str, params: dict[str, Any], destructive: bool, ok: bool, error: str | None) -> None:
    """Append one JSON line per executed action. Never breaks the request."""
    path = settings.audit_log_path
    if not path:
        return
    entry = {
        "ts": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "params": params,
        "destructive": destructive,
        "ok": ok,
        "error": error,
    }
    try:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, default=str) + "\n")
    except Exception as exc:
        logger.warning("Failed to write DevOps audit log to %s: %s", path, exc)

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

ECS:
- list_ecs_clusters      -> {{}}  (optional "region")
- list_ecs_services      -> {{"cluster": "my-cluster"}}  (optional "region")

Load balancers (ELBv2):
- list_elb               -> {{}}  (optional "region"; includes target health)

Route53:
- list_route53_zones     -> {{}}

CloudFront:
- list_cloudfront_distributions -> {{}}

S3 (detail):
- describe_s3_bucket     -> {{"bucket": "my-bucket"}}  (region, versioning, public-access-block, encryption)

Messaging:
- list_sns_topics        -> {{}}  (optional "region")
- list_sqs_queues        -> {{}}  (optional "region", "prefix")

Containers:
- list_ecr_repositories  -> {{}}  (optional "region")

Identity:
- get_caller_identity    -> {{}}  (whoami — account, ARN, user id)

If the user's request doesn't map to a supported action, use action="unsupported".
"""

INTENT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "action": {
            "type": "string",
            "description": "The AWS action to perform",
            "enum": [*SUPPORTED_ACTIONS, "unsupported"],
        },
        "params": {
            "type": "object",
            "description": "Parameters for the action as key-value pairs",
        },
        "is_destructive": {
            "type": "boolean",
            "description": "Whether the action is destructive",
        },
    },
    "required": ["action", "params", "is_destructive"],
}


# ── Intent parsing ──────────────────────────────────────────
async def parse_intent(message: str) -> ParsedIntent:
    data = await generate_structured(
        message,
        system=SYSTEM_PROMPT,
        schema=INTENT_SCHEMA,
        tool_name="return_intent",
        tool_description=(
            "Extract a supported AWS action, params, and destructive flag from the user's request."
        ),
        max_tokens=1024,
    )
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


def _regional_client(service: str, region: str | None = None):
    return boto3.client(
        service,
        region_name=region or settings.aws_default_region,
        **_aws_client_kwargs(),
    )


def _sts_client():
    return boto3.client("sts", **_aws_client_kwargs())


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

        if action == "list_ecs_clusters":
            ecs = _regional_client("ecs", params.get("region"))
            arns = ecs.list_clusters().get("clusterArns", [])
            clusters = []
            if arns:
                desc = ecs.describe_clusters(clusters=arns)
                for c in desc.get("clusters", []):
                    clusters.append(
                        {
                            "name": c.get("clusterName", ""),
                            "arn": c.get("clusterArn", ""),
                            "status": c.get("status", ""),
                            "running_tasks": c.get("runningTasksCount", 0),
                            "pending_tasks": c.get("pendingTasksCount", 0),
                            "active_services": c.get("activeServicesCount", 0),
                            "registered_instances": c.get(
                                "registeredContainerInstancesCount", 0
                            ),
                        }
                    )
            else:
                clusters = [{"arn": a} for a in arns]
            return {"count": len(clusters), "clusters": clusters}

        if action == "list_ecs_services":
            ecs = _regional_client("ecs", params.get("region"))
            cluster = params.get("cluster", "default")
            arns = ecs.list_services(cluster=cluster).get("serviceArns", [])
            services = []
            if arns:
                # describe_services takes at most 10 at a time.
                desc = ecs.describe_services(cluster=cluster, services=arns[:10])
                for s in desc.get("services", []):
                    services.append(
                        {
                            "name": s.get("serviceName", ""),
                            "status": s.get("status", ""),
                            "desired": s.get("desiredCount", 0),
                            "running": s.get("runningCount", 0),
                            "pending": s.get("pendingCount", 0),
                            "launch_type": s.get("launchType", ""),
                            "task_definition": s.get("taskDefinition", ""),
                        }
                    )
            return {"cluster": cluster, "count": len(arns), "services": services}

        if action == "list_elb":
            elb = _regional_client("elbv2", params.get("region"))
            resp = elb.describe_load_balancers()
            load_balancers = []
            for lb in resp.get("LoadBalancers", []):
                lb_arn = lb.get("LoadBalancerArn", "")
                targets = []
                try:
                    tg_resp = elb.describe_target_groups(LoadBalancerArn=lb_arn)
                    for tg in tg_resp.get("TargetGroups", []):
                        health = elb.describe_target_health(
                            TargetGroupArn=tg["TargetGroupArn"]
                        )
                        states = [
                            h["TargetHealth"]["State"]
                            for h in health.get("TargetHealthDescriptions", [])
                        ]
                        healthy = sum(1 for s in states if s == "healthy")
                        targets.append(
                            {
                                "target_group": tg.get("TargetGroupName", ""),
                                "protocol": tg.get("Protocol", ""),
                                "port": tg.get("Port", ""),
                                "total_targets": len(states),
                                "healthy_targets": healthy,
                            }
                        )
                except Exception as exc:  # target health is best-effort
                    logger.warning("ELB target health lookup failed: %s", exc)
                load_balancers.append(
                    {
                        "name": lb.get("LoadBalancerName", ""),
                        "arn": lb_arn,
                        "dns_name": lb.get("DNSName", ""),
                        "type": lb.get("Type", ""),
                        "scheme": lb.get("Scheme", ""),
                        "state": lb.get("State", {}).get("Code", ""),
                        "vpc_id": lb.get("VpcId", ""),
                        "target_groups": targets,
                    }
                )
            return {"count": len(load_balancers), "load_balancers": load_balancers}

        if action == "list_route53_zones":
            r53 = boto3.client("route53", **_aws_client_kwargs())
            resp = r53.list_hosted_zones()
            zones = []
            for z in resp.get("HostedZones", []):
                zones.append(
                    {
                        "id": z.get("Id", "").replace("/hostedzone/", ""),
                        "name": z.get("Name", ""),
                        "private": z.get("Config", {}).get("PrivateZone", False),
                        "record_count": z.get("ResourceRecordSetCount", 0),
                        "comment": z.get("Config", {}).get("Comment", ""),
                    }
                )
            return {"count": len(zones), "zones": zones}

        if action == "list_cloudfront_distributions":
            cf = boto3.client("cloudfront", **_aws_client_kwargs())
            resp = cf.list_distributions()
            dist_list = resp.get("DistributionList", {})
            distributions = []
            for d in dist_list.get("Items", []) or []:
                origins = [
                    o.get("DomainName", "")
                    for o in d.get("Origins", {}).get("Items", [])
                ]
                distributions.append(
                    {
                        "id": d.get("Id", ""),
                        "domain_name": d.get("DomainName", ""),
                        "status": d.get("Status", ""),
                        "enabled": d.get("Enabled", False),
                        "aliases": d.get("Aliases", {}).get("Items", []) or [],
                        "origins": origins,
                        "comment": d.get("Comment", ""),
                    }
                )
            return {"count": len(distributions), "distributions": distributions}

        if action == "describe_s3_bucket":
            s3 = _s3_client()
            bucket = params["bucket"]

            # Region
            try:
                loc = s3.get_bucket_location(Bucket=bucket)
                region = loc.get("LocationConstraint") or "us-east-1"
            except Exception:
                region = ""

            # Versioning
            try:
                ver = s3.get_bucket_versioning(Bucket=bucket)
                versioning = ver.get("Status", "Disabled")
            except Exception:
                versioning = "Unknown"

            # Public access block
            public_access_block = None
            try:
                pab = s3.get_public_access_block(Bucket=bucket)
                public_access_block = pab.get("PublicAccessBlockConfiguration", {})
            except Exception:
                public_access_block = None

            # Encryption
            encryption = None
            try:
                enc = s3.get_bucket_encryption(Bucket=bucket)
                rules = enc.get("ServerSideEncryptionConfiguration", {}).get(
                    "Rules", []
                )
                if rules:
                    default = rules[0].get(
                        "ApplyServerSideEncryptionByDefault", {}
                    )
                    encryption = {
                        "algorithm": default.get("SSEAlgorithm", ""),
                        "kms_key_id": default.get("KMSMasterKeyID", ""),
                    }
            except Exception:
                encryption = None

            return {
                "bucket": bucket,
                "region": region,
                "versioning": versioning,
                "public_access_block": public_access_block,
                "encryption": encryption,
                "encrypted": encryption is not None,
            }

        if action == "list_sns_topics":
            sns = _regional_client("sns", params.get("region"))
            resp = sns.list_topics()
            topics = []
            for t in resp.get("Topics", []):
                arn = t.get("TopicArn", "")
                topics.append({"arn": arn, "name": arn.rsplit(":", 1)[-1]})
            return {"count": len(topics), "topics": topics}

        if action == "list_sqs_queues":
            sqs = _regional_client("sqs", params.get("region"))
            kwargs = {}
            if params.get("prefix"):
                kwargs["QueueNamePrefix"] = params["prefix"]
            resp = sqs.list_queues(**kwargs)
            urls = resp.get("QueueUrls", []) or []
            queues = [
                {"url": u, "name": u.rsplit("/", 1)[-1]} for u in urls
            ]
            return {"count": len(queues), "queues": queues}

        if action == "list_ecr_repositories":
            ecr = _regional_client("ecr", params.get("region"))
            resp = ecr.describe_repositories()
            repos = []
            for r in resp.get("repositories", []):
                repos.append(
                    {
                        "name": r.get("repositoryName", ""),
                        "uri": r.get("repositoryUri", ""),
                        "arn": r.get("repositoryArn", ""),
                        "created": str(r.get("createdAt", "")),
                        "tag_mutability": r.get("imageTagMutability", ""),
                        "scan_on_push": r.get(
                            "imageScanningConfiguration", {}
                        ).get("scanOnPush", False),
                    }
                )
            return {"count": len(repos), "repositories": repos}

        if action == "get_caller_identity":
            sts = _sts_client()
            resp = sts.get_caller_identity()
            return {
                "account": resp.get("Account", ""),
                "arn": resp.get("Arn", ""),
                "user_id": resp.get("UserId", ""),
            }

        return {"error": f"Unsupported action: {action}"}

    return await asyncio.to_thread(_run)


# ── Summarise ───────────────────────────────────────────────
async def summarise(action: str, raw_result: Any) -> str:
    return await generate_text(
        f"Action: {action}\nResult:\n{json.dumps(raw_result, default=str)}",
        system=(
            "You are a senior AWS DevOps engineer. Summarise the following AWS "
            "API result in a clear, concise, human-friendly way. Lead with the "
            "headline count or the single most important fact. Call out anything "
            "operationally noteworthy: stopped/terminated resources, unhealthy "
            "load-balancer targets, buckets without encryption or public-access "
            "block, alarms in ALARM state, or empty results. If the result is an "
            "error, explain it plainly and suggest a likely cause. Keep it to a "
            "few sentences. Use plain text, no markdown."
        ),
        temperature=0.3,
        max_tokens=512,
    )


# ── Public orchestrator ─────────────────────────────────────
async def plan_command(message: str) -> dict:
    """Parse a natural-language command and return the boto3 plan without executing.

    Backs the MCP `aws_plan` tool: external agents may inspect what OmniDev
    would do, but execution — and destructive-action approval — stays in the
    OmniDev UI. Never dispatches, so nothing is audit-logged here.
    """
    intent = await parse_intent(message)
    plan = build_plan(intent)

    if intent.action == "unsupported" or plan is None:
        return {
            "action": intent.action,
            "params": intent.params,
            "plan": None,
            "summary": (
                "Sorry, that action is not currently supported. "
                "Supported services: EC2, S3, VPC, IAM, RDS, CloudWatch, Lambda."
            ),
        }

    return {
        "action": intent.action,
        "params": intent.params,
        "plan": plan,
        "summary": (
            f"Plan preview for {intent.action}. Nothing was executed — "
            "run it from the OmniDev DevOps module to apply."
        ),
    }


async def run_command(message: str, confirm_destructive: bool = False) -> dict:
    intent = await parse_intent(message)
    plan = build_plan(intent)

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
            "plan": None,
        }

    is_destructive = intent.action in DESTRUCTIVE_ACTIONS or intent.is_destructive

    if is_destructive and settings.devops_read_only:
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": (
                "OmniDev is in read-only mode (DEVOPS_READ_ONLY=1). "
                f"Destructive action ({intent.action}) was not executed."
            ),
            "needs_confirmation": False,
            "plan": plan,
        }

    if is_destructive and not confirm_destructive:
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": f"This is a destructive action ({intent.action}). "
            "Please enable 'Confirm destructive actions' and try again.",
            "needs_confirmation": True,
            "plan": plan,
        }

    # Throttle confirmed destructive actions so a runaway caller can't fire
    # an unbounded number of mutating AWS calls in one process lifetime.
    if is_destructive and not _consume_destructive_token():
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": None,
            "summary": (
                "Destructive-action rate limit reached "
                f"(DEVOPS_DESTRUCTIVE_BUCKET={_DESTRUCTIVE_BUCKET_CAPACITY}). "
                "Refused for safety; retry after the bucket is refilled."
            ),
            "needs_confirmation": False,
            "plan": plan,
        }

    try:
        raw_result = await _dispatch(intent)
    except Exception as exc:
        error_msg = str(exc)
        _audit_log(intent.action, intent.params, is_destructive, ok=False, error=error_msg)
        return {
            "action": intent.action,
            "params": intent.params,
            "raw_result": {"error": error_msg},
            "summary": f"AWS call failed: {error_msg}",
            "needs_confirmation": False,
            "plan": plan,
        }

    _audit_log(intent.action, intent.params, is_destructive, ok=True, error=None)

    try:
        summary = await summarise(intent.action, raw_result)
    except Exception as exc:
        logger.warning("Summarise failed for %s: %s", intent.action, exc)
        summary = f"Action {intent.action} completed. See raw result."

    return {
        "action": intent.action,
        "params": intent.params,
        "raw_result": raw_result,
        "summary": summary,
        "needs_confirmation": False,
        "plan": plan,
    }
