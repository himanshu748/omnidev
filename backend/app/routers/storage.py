"""Cloud Storage router — S3 file management."""

from __future__ import annotations

from fastapi import APIRouter, File, Form, Query, UploadFile

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
from app.routers.errors import internal_error

router = APIRouter()


@router.get("/buckets", response_model=BucketListResponse)
async def get_buckets():
    """List all S3 buckets."""
    try:
        buckets = await list_buckets()
        return BucketListResponse(buckets=buckets)
    except Exception as exc:
        raise internal_error("Storage bucket listing failed.") from exc


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
        raise internal_error("Storage file listing failed.") from exc


@router.post("/upload", response_model=UploadResponse)
async def upload(
    file: UploadFile = File(...),
    bucket: str = Form(...),
    key: str = Form(""),
):
    """Upload a file to S3. If key is empty, the original filename is used."""
    resolved_key = key or file.filename or "unnamed"
    data = await file.read()
    try:
        await upload_file(
            bucket=bucket,
            key=resolved_key,
            data=data,
            content_type=file.content_type or "application/octet-stream",
        )
        return UploadResponse(bucket=bucket, key=resolved_key)
    except Exception as exc:
        raise internal_error("Storage upload failed.") from exc


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
        raise internal_error("Storage download URL generation failed.") from exc


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
        raise internal_error("Storage delete failed.") from exc
