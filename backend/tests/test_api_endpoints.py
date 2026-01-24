import sys
import os
from pathlib import Path

from fastapi.testclient import TestClient
from jose import jwt

os.environ["SUPABASE_JWT_SECRET"] = "test-secret"
os.environ["API_KEY_SALT"] = "test-salt"

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.scraper_service import ScrapeResult, scraper_service
from app.services.openai_service import openai_service
from app.routers import location as location_router
from app.services.auth_service import generate_api_key


client = TestClient(app)


def auth_headers(user_id: str = "user-1"):
    token = jwt.encode({"sub": user_id, "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
    api_key = generate_api_key(user_id)
    return {
        "Authorization": f"Bearer {token}",
        "X-API-Key": api_key,
    }


class FakeGeoResult:
    def __init__(self):
        self.ok = True
        self.lat = 19.0760
        self.lng = 72.8777
        self.city = "Mumbai"
        self.state = "MH"
        self.country = "India"
        self.address = "Mumbai, MH, India"
        self.postal = "400001"
        self.neighborhood = "Fort"
        self.json = {"raw": {"address": {"road": "MG Road"}}}


class FakeHttpxResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def json(self):
        return self._payload


class FakeAsyncClient:
    def __init__(self, payload=None, status_code=200):
        self._payload = payload or []
        self._status_code = status_code

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def get(self, *args, **kwargs):
        return FakeHttpxResponse(self._status_code, self._payload)


def test_root_and_health():
    root_res = client.get("/")
    assert root_res.status_code == 200
    assert root_res.json()["status"] == "operational"

    health_res = client.get("/health")
    assert health_res.status_code == 200
    assert health_res.json()["status"] == "healthy"


def test_ai_status_and_chat():
    status_res = client.get("/api/ai/status", headers=auth_headers())
    assert status_res.status_code == 200
    assert status_res.json()["service"] == "OpenAI"

    chat_res = client.post("/api/ai/chat", json={"message": "Hello"}, headers=auth_headers())
    assert chat_res.status_code == 200
    assert "response" in chat_res.json()


def test_vision_status_and_analyze(monkeypatch):
    status_res = client.get("/api/vision/status", headers=auth_headers())
    assert status_res.status_code == 200
    assert status_res.json()["service"] == "OpenAI Vision"

    async def fake_analyze_image(image_data, prompt, api_key=None):
        return "ok"

    monkeypatch.setattr(openai_service, "analyze_image", fake_analyze_image)

    png_bytes = (
        b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
        b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0bIDATx\x9cc`\x00"
        b"\x00\x00\x02\x00\x01\xe2!\xbc3\x00\x00\x00\x00IEND\xaeB`\x82"
    )
    files = {"file": ("pixel.png", png_bytes, "image/png")}
    analyze_res = client.post("/api/vision/analyze", files=files, headers=auth_headers())
    assert analyze_res.status_code == 200
    assert analyze_res.json()["analysis"] == "ok"


def test_scraper_endpoints(monkeypatch):
    async def fake_scrape(url, wait_time_ms=2000, capture_screenshot=False, extract_selector=None, wait_for_selector=None):
        return ScrapeResult(
            success=True,
            url=url,
            title="Example",
            html="<html></html>",
            text="Example",
            screenshot="abc" if capture_screenshot else None,
            error=None,
            engine="playwright",
            load_time_ms=10,
        )

    async def fake_cleanup():
        return None

    monkeypatch.setattr(scraper_service, "scrape", fake_scrape)
    monkeypatch.setattr(scraper_service, "take_screenshot", lambda url: fake_scrape(url, capture_screenshot=True))
    monkeypatch.setattr(scraper_service, "cleanup", fake_cleanup)

    status_res = client.get("/api/scraper/status", headers=auth_headers())
    assert status_res.status_code == 200
    assert "playwright" in status_res.json()

    scrape_res = client.post("/api/scraper/scrape", json={"url": "https://example.com"}, headers=auth_headers())
    assert scrape_res.status_code == 200
    assert scrape_res.json()["success"] is True

    screenshot_res = client.post("/api/scraper/screenshot", json={"url": "https://example.com"}, headers=auth_headers())
    assert screenshot_res.status_code == 200
    assert screenshot_res.json()["screenshot"] == "abc"

    cleanup_res = client.post("/api/scraper/cleanup", headers=auth_headers())
    assert cleanup_res.status_code == 200
    assert cleanup_res.json()["status"] == "success"


def test_location_endpoints(monkeypatch):
    monkeypatch.setattr(location_router.geocoder, "ip", lambda *_args, **_kwargs: FakeGeoResult())
    monkeypatch.setattr(location_router.geocoder, "osm", lambda *_args, **_kwargs: FakeGeoResult())
    monkeypatch.setattr(
        location_router.httpx,
        "AsyncClient",
        lambda *args, **kwargs: FakeAsyncClient(
            payload=[{"lat": "19.0760", "lon": "72.8777", "display_name": "Mumbai", "address": {"city": "Mumbai", "state": "MH", "country": "India"}}]
        ),
    )

    current_res = client.get("/api/location/current", headers=auth_headers())
    assert current_res.status_code == 200
    assert current_res.json()["city"] == "Mumbai"

    reverse_res = client.get("/api/location/reverse", params={"lat": 19.0760, "lng": 72.8777}, headers=auth_headers())
    assert reverse_res.status_code == 200
    assert reverse_res.json()["city"] == "Mumbai"

    search_res = client.get("/api/location/search", params={"query": "Mumbai"}, headers=auth_headers())
    assert search_res.status_code == 200
    assert search_res.json()["city"] == "Mumbai"

    nearby_res = client.get("/api/location/nearby", params={"lat": 19.0760, "lng": 72.8777}, headers=auth_headers())
    assert nearby_res.status_code == 200
    assert nearby_res.json()["city"] == "Mumbai"

    status_res = client.get("/api/location/status", headers=auth_headers())
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "operational"


def test_devops_endpoints():
    caps_res = client.get("/api/devops/capabilities", headers=auth_headers())
    assert caps_res.status_code == 200
    assert caps_res.json()["name"] == "OmniDev DevOps Agent"

    ec2_res = client.get("/api/devops/ec2/instances", headers=auth_headers())
    assert ec2_res.status_code == 200

    s3_res = client.get("/api/devops/s3/buckets", headers=auth_headers())
    assert s3_res.status_code == 200

    s3_objects_res = client.get("/api/devops/s3/objects/test-bucket", headers=auth_headers())
    assert s3_objects_res.status_code == 200


def test_storage_endpoints():
    status_res = client.get("/api/storage/status", headers=auth_headers())
    assert status_res.status_code == 200
    assert status_res.json()["service"] == "S3 Storage"

    buckets_res = client.get("/api/storage/buckets", headers=auth_headers())
    assert buckets_res.status_code == 200

    objects_res = client.get("/api/storage/buckets/test-bucket/objects", headers=auth_headers())
    assert objects_res.status_code == 200

    files = {"file": ("hello.txt", b"hello", "text/plain")}
    upload_res = client.post("/api/storage/upload", data={"bucket_name": "test-bucket"}, files=files, headers=auth_headers())
    assert upload_res.status_code == 503

    download_res = client.get("/api/storage/download/test-bucket/hello.txt", headers=auth_headers())
    assert download_res.status_code == 503

    delete_res = client.delete("/api/storage/delete/test-bucket/hello.txt", headers=auth_headers())
    assert delete_res.status_code == 503


def test_auth_api_key():
    headers = auth_headers("user-2")
    api_key_res = client.post("/api/auth/api-key", headers={"Authorization": headers["Authorization"]})
    assert api_key_res.status_code == 200
    assert "api_key" in api_key_res.json()
