"""Every API route is listed in EXPECTED_ENDPOINTS, so the coverage report
(and the full-run check in conftest.py) cannot silently miss a new endpoint."""

from app.main import app
from tests.conftest import EXPECTED_ENDPOINTS

# Framework and protocol routes outside the JSON API surface.
NOT_TRACKED = {"GET /openapi.json", "GET /docs", "GET /redoc"}


def _api_operations() -> set[str]:
    schema = app.openapi()
    return {
        f"{method.upper()} {path}"
        for path, operations in schema["paths"].items()
        for method in operations
    } - NOT_TRACKED


def test_every_route_is_tracked():
    missing = sorted(_api_operations() - set(EXPECTED_ENDPOINTS))
    assert not missing, (
        "Add these routes to EXPECTED_ENDPOINTS in tests/conftest.py and cover them "
        f"with coverage_tracker(...): {missing}"
    )


def test_no_stale_entries():
    stale = sorted(set(EXPECTED_ENDPOINTS) - _api_operations())
    assert not stale, f"EXPECTED_ENDPOINTS lists routes that no longer exist: {stale}"


def test_entries_are_unique():
    assert len(EXPECTED_ENDPOINTS) == len(set(EXPECTED_ENDPOINTS))
