import boto3
import pytest
from moto import mock_aws

from app.config import settings
from app.services import storage_service


@pytest.mark.asyncio
async def test_storage_service_round_trip(monkeypatch):
    with mock_aws():
        monkeypatch.setattr(settings, "aws_access_key_id", "test")
        monkeypatch.setattr(settings, "aws_secret_access_key", "test")
        monkeypatch.setattr(settings, "aws_default_region", "us-east-1")
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="demo-bucket")

        await storage_service.upload_file("demo-bucket", "notes.txt", b"hello", "text/plain")
        obj = s3.get_object(Bucket="demo-bucket", Key="notes.txt")
        assert obj["Body"].read() == b"hello"

        buckets = await storage_service.list_buckets()
        assert buckets[0]["name"] == "demo-bucket"

        files = await storage_service.list_files("demo-bucket")
        assert files[0]["key"] == "notes.txt"

        url = await storage_service.presigned_download_url("demo-bucket", "notes.txt", 600)
        assert "demo-bucket" in url

        await storage_service.delete_file("demo-bucket", "notes.txt")
        files_after = await storage_service.list_files("demo-bucket")
        assert files_after == []
