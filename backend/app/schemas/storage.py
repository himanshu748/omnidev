"""Schemas for the Cloud Storage module."""

from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class BucketInfo(BaseModel):
    name: str
    creation_date: datetime | None = None


class BucketListResponse(BaseModel):
    buckets: list[BucketInfo]


class FileInfo(BaseModel):
    key: str
    size: int = 0
    last_modified: datetime | None = None
    storage_class: str = ""


class FileListResponse(BaseModel):
    bucket: str
    prefix: str = ""
    files: list[FileInfo]


class UploadResponse(BaseModel):
    bucket: str
    key: str
    message: str = "Upload successful"


class DownloadResponse(BaseModel):
    bucket: str
    key: str
    presigned_url: str
    expires_in: int = Field(3600, description="URL expiry in seconds")


class DeleteResponse(BaseModel):
    bucket: str
    key: str
    message: str = "Deleted"
