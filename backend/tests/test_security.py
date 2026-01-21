import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient
from jose import jwt

os.environ["SUPABASE_JWT_SECRET"] = "test-secret"
os.environ["API_KEY_SALT"] = "test-salt"

sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.main import app
from app.services.auth_service import generate_api_key


client = TestClient(app)


def test_requires_auth_header():
    res = client.get("/api/ai/status")
    assert res.status_code == 401


def test_requires_api_key():
    token = jwt.encode({"sub": "user-3", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
    res = client.get("/api/ai/status", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 403


def test_allows_valid_api_key():
    token = jwt.encode({"sub": "user-4", "role": "user"}, os.environ["SUPABASE_JWT_SECRET"], algorithm="HS256")
    api_key = generate_api_key("user-4")
    res = client.get("/api/ai/status", headers={"Authorization": f"Bearer {token}", "X-API-Key": api_key})
    assert res.status_code == 200
