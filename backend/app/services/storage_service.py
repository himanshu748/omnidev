"""
Cloud Storage service — S3 operations.
All boto3 calls wrapped in asyncio.to_thread.
"""

from __future__ import annotations

import asyncio
from typing import Any

import boto3

from app.config import settings


def _s3_client():
    return boto3.client(
        "s3",
        region_name=settings.aws_default_region,
        aws_access_key_id=settings.aws_access_key_id,
        aws_secret_access_key=settings.aws_secret_access_key,
    )


# ── List buckets ────────────────────────────────────────────
async def list_buckets() -> list[dict[str, Any]]:
    def _run():
        s3 = _s3_client()
        resp = s3.list_buckets()
        return [
            {
                "name": b["Name"],
                "creation_date": b.get("CreationDate"),
            }
            for b in resp.get("Buckets", [])
        ]

    return await asyncio.to_thread(_run)


# ── List files in bucket ───────────────────────────────────
async def list_files(bucket: str, prefix: str = "") -> list[dict[str, Any]]:
    def _run():
        s3 = _s3_client()
        kwargs: dict[str, Any] = {"Bucket": bucket}
        if prefix:
            kwargs["Prefix"] = prefix
        resp = s3.list_objects_v2(**kwargs)
        return [
            {
                "key": obj["Key"],
                "size": obj["Size"],
                "last_modified": obj.get("LastModified"),
                "storage_class": obj.get("StorageClass", ""),
            }
            for obj in resp.get("Contents", [])
        ]

    return await asyncio.to_thread(_run)


# ── Upload file ─────────────────────────────────────────────
async def upload_file(
    bucket: str,
    key: str,
    data: bytes,
    content_type: str = "application/octet-stream",
) -> None:
    def _run():
        s3 = _s3_client()
        s3.put_object(Bucket=bucket, Key=key, Body=data, ContentType=content_type)

    await asyncio.to_thread(_run)


# ── Generate presigned download URL ─────────────────────────
async def presigned_download_url(
    bucket: str, key: str, expires_in: int = 3600
) -> str:
    def _run():
        s3 = _s3_client()
        return s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=expires_in,
        )

    return await asyncio.to_thread(_run)


# ── Delete object ───────────────────────────────────────────
async def delete_file(bucket: str, key: str) -> None:
    def _run():
        s3 = _s3_client()
        s3.delete_object(Bucket=bucket, Key=key)

    await asyncio.to_thread(_run)
