import pytest

from app.services import location_service


def test_parse_ipinfo():
    data = {
        "ip": "1.1.1.1",
        "city": "Test",
        "region": "CA",
        "country": "US",
        "postal": "12345",
        "loc": "10.5,20.5",
        "timezone": "UTC",
        "org": "Test Org",
    }
    parsed = location_service._parse_ipinfo(data)
    assert parsed["latitude"] == 10.5
    assert parsed["longitude"] == 20.5


def test_parse_nominatim_search_response():
    data = [
        {
            "display_name": "Place",
            "lat": "1.0",
            "lon": "2.0",
            "type": "city",
            "address": {"city": "Place"},
        }
    ]
    results = location_service._parse_nominatim_search_response(data)
    assert results[0]["display_name"] == "Place"


@pytest.mark.asyncio
async def test_location_endpoints(client, monkeypatch, coverage_tracker):
    async def fake_ip_lookup(ip=None):
        return {
            "ip": ip or "1.1.1.1",
            "city": "Test",
            "region": "CA",
            "country": "US",
            "postal": "12345",
            "latitude": 1.0,
            "longitude": 2.0,
            "timezone": "UTC",
            "org": "Test Org",
        }

    async def fake_reverse_geocode(lat: float, lng: float):
        return {
            "latitude": lat,
            "longitude": lng,
            "display_name": "Test Address",
            "address": {"city": "Test"},
        }

    async def fake_geocode(query: str, limit: int = 5, countrycodes: str | None = None):
        return [
            {
                "display_name": "Test Place",
                "latitude": 1.0,
                "longitude": 2.0,
                "type": "place",
                "address": {"city": "Test"},
            }
        ]

    async def fake_my_location():
        return {
            "ip": "1.1.1.1",
            "city": "Test",
            "region": "CA",
            "country": "US",
            "latitude": 1.0,
            "longitude": 2.0,
        }

    monkeypatch.setattr(location_service, "ip_lookup", fake_ip_lookup)
    monkeypatch.setattr(location_service, "reverse_geocode", fake_reverse_geocode)
    monkeypatch.setattr(location_service, "geocode", fake_geocode)
    monkeypatch.setattr(location_service, "my_location", fake_my_location)

    resp = await client.get("/api/location/ip?ip=1.1.1.1")
    assert resp.status_code == 200
    coverage_tracker("GET /api/location/ip")

    resp = await client.get("/api/location/reverse?lat=1&lng=2")
    assert resp.status_code == 200
    coverage_tracker("GET /api/location/reverse")

    resp = await client.get("/api/location/geocode?q=Test")
    assert resp.status_code == 200
    coverage_tracker("GET /api/location/geocode")

    resp = await client.get("/api/location/me")
    assert resp.status_code == 200
    coverage_tracker("GET /api/location/me")
