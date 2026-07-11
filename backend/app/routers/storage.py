"""Cloud Storage router — S3 file management."""

from __future__ import annotations

from botocore.exceptions import NoCredentialsError, PartialCredentialsError
from fastapi import APIRouter, File, Form, HTTPException, Query, UploadFile

from app.config import settings
from app.schemas.storage import (
    BucketListResponse,
    DeleteResponse,
    DownloadResponse,
    FileListResponse,
    UploadResponse,
)
from app.services.storage_service import (
    delete_file,
    list_buckets,
    list_files,
    presigned_download_url,
    upload_file,
)
from app.routers.errors import internal_error, service_unavailable

router = APIRouter()


def _storage_error(exc: Exception, detail: str) -> Exception:
    if isinstance(exc, (NoCredentialsError, PartialCredentialsError)):
        return service_unavailable(
            "AWS credentials are not configured. Set AWS_ACCESS_KEY_ID/AWS_SECRET_ACCESS_KEY or configure an AWS profile."
        )
    return internal_error(detail)


@router.get("/buckets", response_model=BucketListResponse)
async def get_buckets():
    """List all S3 buckets."""
    try:
        buckets = await list_buckets()
        return BucketListResponse(buckets=buckets)
    except Exception as exc:
        raise _storage_error(exc, "Storage bucket listing failed.") from exc


@router.get("/files", response_model=FileListResponse)
async def get_files(
    bucket: str = Query(...),
    prefix: str = Query(""),
):
    """List objects in an S3 bucket with optional prefix filter."""
    try:
        files = await list_files(bucket, prefix)
        return FileListResponse(bucket=bucket, prefix=prefix, files=files)
    except Exception as exc:
        raise _storage_error(exc, "Storage file listing failed.") from exc


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    bucket: str = Form(...),
    key: str = Form(""),
):
    """Upload a file to S3. If key is empty, the original filename is used."""
    resolved_key = key or file.filename or "unnamed"

    # Read in bounded chunks so an oversized body is rejected without buffering
    # the whole thing into memory.
    max_bytes = settings.max_upload_mb * 1024 * 1024
    chunks: list[bytes] = []
    total = 0
    while chunk := await file.read(1024 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=413,
                detail=f"Upload exceeds the {settings.max_upload_mb} MB limit.",
            )
        chunks.append(chunk)
    data = b"".join(chunks)
    try:
        await upload_file(
            bucket=bucket,
            key=resolved_key,
            data=data,
            content_type=file.content_type or "application/octet-stream",
        )
        return UploadResponse(bucket=bucket, key=resolved_key)
    except Exception as exc:
        raise _storage_error(exc, "Storage upload failed.") from exc


@router.get("/download", response_model=DownloadResponse)
async def download(
    bucket: str = Query(...),
    key: str = Query(...),
    expires_in: int = Query(3600, ge=60, le=86400),
):
    """Generate a presigned download URL for an S3 object."""
    try:
        url = await presigned_download_url(bucket, key, expires_in)
        return DownloadResponse(
            bucket=bucket, key=key, presigned_url=url, expires_in=expires_in
        )
    except Exception as exc:
        raise _storage_error(exc, "Storage download URL generation failed.") from exc


@router.delete("/files", response_model=DeleteResponse)
async def delete(
    bucket: str = Query(...),
    key: str = Query(...),
):
    """Delete an object from S3."""
    try:
        await delete_file(bucket, key)
        return DeleteResponse(bucket=bucket, key=key)
    except Exception as exc:
        raise _storage_error(exc, "Storage delete failed.") from exc
