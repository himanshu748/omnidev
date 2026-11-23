"""Keep native-client decoding fixtures valid against the real backend schemas."""

import json
from pathlib import Path

import pytest
from app.schemas.codegen import CodeGenResponse
from app.schemas.devops import DevOpsCommandResponse
from app.schemas.scraper import ScrapeResponse
from pydantic import BaseModel


@pytest.mark.parametrize(
    ("name", "schema"),
    [
        ("devops", DevOpsCommandResponse),
        ("codegen", CodeGenResponse),
        ("scraper", ScrapeResponse),
    ],
)
def test_swift_response_fixture_matches_backend_schema(
    name: str, schema: type[BaseModel]
) -> None:
    fixtures = (
        Path(__file__).resolve().parents[2] / "macos/Tests/OmniDevMacTests/Fixtures"
    )
    payload = json.loads((fixtures / f"{name}.json").read_text(encoding="utf-8"))
    assert set(payload) <= set(schema.model_fields)
    schema.model_validate(payload)
