import pytest
from botocore.exceptions import NoCredentialsError

from app.routers import storage as storage_router


@pytest.mark.asyncio
async def test_storage_endpoints(client, monkeypatch, coverage_tracker):
    async def fake_list_buckets():
        return [{"name": "demo", "creation_date": None}]

    async def fake_list_files(bucket: str, prefix: str = ""):
        return [{"key": "file.txt", "size": 12, "last_modified": None, "storage_class": "STANDARD"}]

    async def fake_upload_file(bucket: str, key: str, data: bytes, content_type: str = "application/octet-stream"):
        return None

    async def fake_presigned_download_url(bucket: str, key: str, expires_in: int = 3600):
        return "https://example.com/file.txt"

    async def fake_delete_file(bucket: str, key: str):
        return None

    monkeypatch.setattr(storage_router, "list_buckets", fake_list_buckets)
    monkeypatch.setattr(storage_router, "list_files", fake_list_files)
    monkeypatch.setattr(storage_router, "upload_file", fake_upload_file)
    monkeypatch.setattr(storage_router, "presigned_download_url", fake_presigned_download_url)
    monkeypatch.setattr(storage_router, "delete_file", fake_delete_file)

    resp = await client.get("/api/storage/buckets")
    assert resp.status_code == 200
    assert resp.json()["buckets"][0]["name"] == "demo"
    coverage_tracker("GET /api/storage/buckets")

    resp = await client.get("/api/storage/files?bucket=demo&prefix=")
    assert resp.status_code == 200
    assert resp.json()["files"][0]["key"] == "file.txt"
    coverage_tracker("GET /api/storage/files")

    resp = await client.post(
        "/api/storage/upload",
        data={"bucket": "demo", "key": "file.txt"},
        files={"file": ("file.txt", b"data", "text/plain")},
    )
    assert resp.status_code == 200
    coverage_tracker("POST /api/storage/upload")

    resp = await client.get("/api/storage/download?bucket=demo&key=file.txt&expires_in=3600")
    assert resp.status_code == 200
    assert resp.json()["presigned_url"].startswith("https://")
    coverage_tracker("GET /api/storage/download")

    resp = await client.delete("/api/storage/files?bucket=demo&key=file.txt")
    assert resp.status_code == 200
    coverage_tracker("DELETE /api/storage/files")


@pytest.mark.asyncio
async def test_upload_rejects_oversize_body(client, monkeypatch):
    from app.config import settings

    async def fake_upload_file(**kwargs):
        return None

    monkeypatch.setattr(storage_router, "upload_file", fake_upload_file)
    monkeypatch.setattr(settings, "max_upload_mb", 1)

    big = b"x" * (2 * 1024 * 1024)  # 2 MB > 1 MB cap
    resp = await client.post(
        "/api/storage/upload",
        data={"bucket": "demo", "key": "big.bin"},
        files={"file": ("big.bin", big, "application/octet-stream")},
    )
    assert resp.status_code == 413
    assert "limit" in resp.json()["detail"].lower()


@pytest.mark.asyncio
async def test_storage_download_validation(client):
    resp = await client.get("/api/storage/download?bucket=demo&key=file.txt&expires_in=10")
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_storage_returns_503_without_aws_credentials(client, monkeypatch):
    async def fake_list_buckets():
        raise NoCredentialsError()

    monkeypatch.setattr(storage_router, "list_buckets", fake_list_buckets)

    resp = await client.get("/api/storage/buckets")

    assert resp.status_code == 503
    assert "AWS credentials" in resp.json()["detail"]
