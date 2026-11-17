"""Filesystem regressions for atomic, serialized agent backup publication."""

import json
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from app.services import agent_backups as backups


def test_failed_serialization_preserves_previous_manifest(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    manifest = backups._manifest_path()
    before = manifest.read_bytes()
    with pytest.raises(TypeError):
        backups._write_manifest([{**record, "reason": "changed"}, {"unserializable": object()}])
    assert manifest.read_bytes() == before
    assert set(backups._root().iterdir()) == {manifest, Path(record["backup_path"])}


def test_failed_replace_preserves_manifest_and_referenced_backup(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("first")
    original = backups.snapshot(target)
    manifest = backups._manifest_path()
    before = manifest.read_bytes()
    monkeypatch.setattr(backups, "MAX_BACKUPS", 1)
    real_replace = backups.os.replace

    def fail_manifest_replace(source, destination):
        if Path(destination) == manifest:
            raise OSError("sensitive injected details must not escape")
        return real_replace(source, destination)

    monkeypatch.setattr(backups.os, "replace", fail_manifest_replace)
    target.write_text("second")
    failed = backups.snapshot(target)
    assert failed["backed_up"] is False
    assert "sensitive" not in failed["note"]
    assert manifest.read_bytes() == before
    assert Path(original["backup_path"]).read_text() == "first"
    assert set(backups._root().iterdir()) == {manifest, Path(original["backup_path"])}
    backups.restore(original["id"])
    assert target.read_text() == "first"


def test_failed_manifest_write_does_not_delete_expired_files(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("first")
    original = backups.snapshot(target)
    manifest = backups._manifest_path()
    before = manifest.read_bytes()
    monkeypatch.setattr(backups, "MAX_BACKUPS", 1)

    def fail_write(records):
        raise OSError("injected write failure")

    monkeypatch.setattr(backups, "_write_manifest", fail_write)
    target.write_text("second")
    failed = backups.snapshot(target)
    assert failed["backed_up"] is False
    assert manifest.read_bytes() == before
    assert Path(original["backup_path"]).read_text() == "first"
    assert set(backups._root().iterdir()) == {manifest, Path(original["backup_path"])}


def test_retention_publishes_before_unlinking(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("first")
    original = backups.snapshot(target)
    monkeypatch.setattr(backups, "MAX_BACKUPS", 1)
    real_unlink = Path.unlink
    observed = []

    def inspect_unlink(path, *args, **kwargs):
        if path == Path(original["backup_path"]):
            ids = {r["id"] for r in backups._load_manifest()}
            assert original["id"] not in ids
            observed.append(path)
        return real_unlink(path, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", inspect_unlink)
    target.write_text("second")
    newest = backups.snapshot(target)
    assert newest["backed_up"] is True
    assert observed
    assert [r["id"] for r in backups.list_backups()] == [newest["id"]]


def test_age_and_count_retention_keep_valid_restore_records(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("expired")
    old = backups.snapshot(target)
    records = backups._load_manifest()
    records[0]["created_at"] = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    backups._write_manifest(records)
    monkeypatch.setattr(backups, "MAX_BACKUPS", 2)
    created = []
    for content in ("one", "two", "three"):
        target.write_text(content)
        created.append(backups.snapshot(target))
    kept = backups.list_backups()
    assert [r["id"] for r in kept] == [created[2]["id"], created[1]["id"]]
    assert not Path(old["backup_path"]).exists()
    assert not Path(created[0]["backup_path"]).exists()
    backups.restore(created[1]["id"])
    assert target.read_text() == "two"


def test_concurrent_snapshots_pruning_listing_and_restore(tmp_path, monkeypatch):
    monkeypatch.setattr(backups, "MAX_BACKUPS", 8)
    paths = []
    for i in range(32):
        path = tmp_path / f"source-{i}.txt"
        path.write_text(f"content-{i}")
        paths.append(path)

    def snapshot_and_list(path):
        record = backups.snapshot(path)
        assert record["backed_up"] is True
        for entry in backups.list_backups():
            assert entry["id"]
        return record

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(snapshot_and_list, paths))
    raw_lines = backups._manifest_path().read_text().splitlines()
    records = [json.loads(line) for line in raw_lines]
    assert len(records) == 8
    assert len({r["id"] for r in records}) == 8
    assert {r["id"] for r in records} <= {r["id"] for r in results}
    for record in records:
        assert Path(record["backup_path"]).read_text() == Path(record["path"]).read_text()
    with ThreadPoolExecutor(max_workers=8) as pool:
        restored = list(pool.map(backups.restore, [r["id"] for r in records]))
    assert len(restored) == 8
    assert len(list(backups._root().iterdir())) == 9  # eight snapshots plus manifest
