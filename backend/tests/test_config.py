from app.config import Settings


def test_cors_origin_list_keeps_explicit_http_origins_first():
    settings = Settings(
        cors_origins="https://app.example.com,http://localhost:3000,https://api.example.com/"
    )

    assert settings.cors_origin_list[:3] == [
        "https://app.example.com",
        "http://localhost:3000",
        "https://api.example.com",
    ]
    assert len(settings.cors_origin_list) == len(set(settings.cors_origin_list))


def test_cors_origin_list_ignores_wildcards_and_malformed_origins():
    settings = Settings(
        cors_origins="*,javascript:alert(1),example.com,https://ok.example.com/path,https://app.example.com"
    )

    assert "*" not in settings.cors_origin_list
    assert "javascript:alert(1)" not in settings.cors_origin_list
    assert "example.com" not in settings.cors_origin_list
    assert "https://ok.example.com/path" not in settings.cors_origin_list
    assert settings.cors_origin_list[0] == "https://app.example.com"
