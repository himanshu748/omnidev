"""Security invariants for local state containing chats, paths, and excerpts."""

import os

import pytest

from app.services import data_paths


def test_private_paths_are_owner_only(tmp_path, monkeypatch):
    monkeypatch.setattr(data_paths.settings, "data_dir", str(tmp_path / "state"))

    root = data_paths.private_data_root()
    runtime = data_paths.private_subdir("mcp-runtime", "fetch")
    config = root / "config.json"
    data_paths.write_private_text(config, '{"secret": "local"}')

    assert root.stat().st_mode & 0o777 == 0o700
    assert runtime.stat().st_mode & 0o777 == 0o700
    assert config.stat().st_mode & 0o777 == 0o600


def test_private_subdir_cannot_escape_data_root(tmp_path, monkeypatch):
    monkeypatch.setattr(data_paths.settings, "data_dir", str(tmp_path / "state"))

    with pytest.raises(ValueError, match="escapes DATA_DIR"):
        data_paths.private_subdir("..", "outside")


@pytest.mark.skipif(not hasattr(os, "O_NOFOLLOW"), reason="platform lacks O_NOFOLLOW")
def test_private_write_refuses_symlink(tmp_path, monkeypatch):
    monkeypatch.setattr(data_paths.settings, "data_dir", str(tmp_path / "state"))
    root = data_paths.private_data_root()
    outside = tmp_path / "outside.txt"
    outside.write_text("unchanged")
    link = root / "config.json"
    link.symlink_to(outside)

    with pytest.raises(OSError):
        data_paths.write_private_text(link, "overwritten")
    assert outside.read_text() == "unchanged"
