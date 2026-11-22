"""Restoring an agent snapshot must preserve independent destination edits."""

from pathlib import Path

import pytest

from app.services import agent_backups as backups


def test_independent_edit_requires_explicit_overwrite(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("newer independent work")

    with pytest.raises(ValueError, match="(?i)conflict"):
        backups.restore(record["id"])

    assert target.read_text() == "newer independent work"
    assert not list(tmp_path.glob(".restore-*"))


def test_recreated_file_is_not_the_expected_destination(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.rename(tmp_path / "old-source.txt")
    target.write_text("replacement")

    with pytest.raises(ValueError, match="(?i)conflict"):
        backups.restore(record["id"])

    assert target.read_text() == "replacement"


@pytest.mark.asyncio
async def test_restore_endpoint_reports_conflict_without_clobbering(client, tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("newer independent work")

    response = await client.post(f"/api/agent/backups/{record['id']}/restore")

    assert response.status_code == 409
    assert "force" in response.json()["detail"]
    assert "newer independent work" not in response.text
    assert target.read_text() == "newer independent work"


def test_completed_agent_output_and_repeated_restore(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original\n")
    record = backups.snapshot(target)
    target.write_text("agent output\n")
    assert backups.record_completed_edit(record["id"], "agent output\n")

    backups.restore(record["id"])
    assert target.read_text() == "original\n"
    first_restored_stat = target.stat()
    backups.restore(record["id"])
    assert target.stat() == first_restored_stat
    assert not list(tmp_path.glob(".restore-*"))


def test_same_agent_bytes_recreated_by_another_writer_need_force(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("agent output")
    assert backups.record_completed_edit(record["id"], "agent output")
    target.rename(tmp_path / "previous-agent-output.txt")
    target.write_text("agent output")
    with pytest.raises(backups.RestoreConflict):
        backups.restore(record["id"])
    assert target.read_text() == "agent output"
    backups.restore(record["id"], force=True)
    assert target.read_text() == "original"


@pytest.mark.parametrize("legacy", [False, True])
def test_missing_destination_can_be_recreated_without_overwriting_work(tmp_path, legacy):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    if legacy:
        record.pop("original_sha256")
        record.pop("expected_target")
        backups._write_manifest([record])
    target.unlink()
    backups.restore(record["id"])
    assert target.read_text() == "original"


def test_legacy_existing_destination_requires_force(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    record.pop("original_sha256")
    record.pop("expected_target")
    backups._write_manifest([record])
    target.write_text("unknown newer work")
    with pytest.raises(backups.RestoreConflict, match="unknown"):
        backups.restore(record["id"])
    assert target.read_text() == "unknown newer work"
    backups.restore(record["id"], force=True)
    assert target.read_text() == "original"


@pytest.mark.parametrize("force", [False, True])
@pytest.mark.parametrize("dangling", [False, True])
def test_destination_symlink_is_never_followed(tmp_path, force, dangling):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    elsewhere = tmp_path / "elsewhere.txt"
    if not dangling:
        elsewhere.write_text("unrelated work")
    target.unlink()
    target.symlink_to(elsewhere)
    with pytest.raises(backups.RestoreConflict, match="symlink"):
        backups.restore(record["id"], force=force)
    assert target.is_symlink()
    if dangling:
        assert not elsewhere.exists()
    else:
        assert elsewhere.read_text() == "unrelated work"


def test_replaced_parent_symlink_is_not_followed_even_with_force(tmp_path):
    parent = tmp_path / "project"
    parent.mkdir()
    target = parent / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    parent.rename(tmp_path / "old-project")
    elsewhere = tmp_path / "unrelated-project"
    elsewhere.mkdir()
    (elsewhere / "source.txt").write_text("unrelated work")
    parent.symlink_to(elsewhere, target_is_directory=True)
    with pytest.raises(backups.RestoreConflict, match="symlink"):
        backups.restore(record["id"], force=True)
    assert (elsewhere / "source.txt").read_text() == "unrelated work"


@pytest.mark.parametrize("force", [False, True])
def test_edit_during_staging_is_preserved_even_after_initial_force(tmp_path, monkeypatch, force):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("agent output")
    assert backups.record_completed_edit(record["id"], "agent output")
    copy2 = backups.shutil.copy2

    def copy_then_independent_edit(source, destination):
        result = copy2(source, destination)
        target.write_text("arrived during restore")
        return result

    monkeypatch.setattr(backups.shutil, "copy2", copy_then_independent_edit)
    with pytest.raises(backups.RestoreConflict, match="during restore"):
        backups.restore(record["id"], force=force)
    assert target.read_text() == "arrived during restore"
    assert not list(tmp_path.glob(".restore-*"))


@pytest.mark.parametrize("operation", ["copy", "replace"])
def test_failed_restore_preserves_destination_and_removes_stage(tmp_path, monkeypatch, operation):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("agent output")
    assert backups.record_completed_edit(record["id"], "agent output")

    def fail(*args, **kwargs):
        if operation == "copy":
            args[1].write_text("partial snapshot bytes")
        raise OSError("sensitive injected failure")

    monkeypatch.setattr(
        backups.shutil if operation == "copy" else backups.os,
        "copy2" if operation == "copy" else "replace",
        fail,
    )
    with pytest.raises(backups.RestoreError, match="Could not restore") as error:
        backups.restore(record["id"])
    assert "sensitive" not in str(error.value)
    assert target.read_text() == "agent output"
    assert not list(tmp_path.glob(".restore-*"))
    assert backups.list_backups()[0]["id"] == record["id"]


def test_corrupted_snapshot_is_not_published(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("agent output")
    assert backups.record_completed_edit(record["id"], "agent output")
    Path(record["backup_path"]).write_text("corrupted")
    with pytest.raises(backups.RestoreError, match="fingerprint"):
        backups.restore(record["id"])
    assert target.read_text() == "agent output"
    assert not list(tmp_path.glob(".restore-*"))


def test_failed_completed_state_publication_keeps_conflict_guard(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    before = backups._manifest_path().read_bytes()
    target.write_text("agent output")

    def fail_write(records):
        raise OSError("sensitive details")

    monkeypatch.setattr(backups, "_write_manifest", fail_write)
    assert backups.record_completed_edit(record["id"], "agent output") is False
    assert backups._manifest_path().read_bytes() == before
    with pytest.raises(backups.RestoreConflict):
        backups.restore(record["id"])
    assert target.read_text() == "agent output"


def test_independent_edit_is_not_registered_as_agent_output(tmp_path):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    before = backups._manifest_path().read_bytes()
    target.write_text("independent output")
    assert backups.record_completed_edit(record["id"], "intended agent output") is False
    assert backups._manifest_path().read_bytes() == before
    with pytest.raises(backups.RestoreConflict):
        backups.restore(record["id"])


@pytest.mark.asyncio
async def test_restore_endpoint_requires_explicit_force_and_retains_unknown_404(client, tmp_path, coverage_tracker):
    target = tmp_path / "source.txt"
    target.write_text("original")
    record = backups.snapshot(target)
    target.write_text("independent output")
    listed = await client.get("/api/agent/backups")
    assert listed.status_code == 200
    assert listed.json()["backups"][0]["id"] == record["id"]
    coverage_tracker("GET /api/agent/backups")
    coverage_tracker("POST /api/agent/backups/{backup_id}/restore")
    endpoint = f"/api/agent/backups/{record['id']}/restore"
    assert (await client.post(endpoint)).status_code == 409
    assert (await client.post(endpoint + "?force=false")).status_code == 409
    assert target.read_text() == "independent output"
    response = await client.post(endpoint + "?force=true")
    assert response.status_code == 200
    assert response.json()["restored_to"] == str(target)
    assert target.read_text() == "original"
    assert (await client.post("/api/agent/backups/unknown/restore?force=true")).status_code == 404


def test_snapshot_race_does_not_publish_mismatched_original(tmp_path, monkeypatch):
    target = tmp_path / "source.txt"
    target.write_text("original")
    copy2 = backups.shutil.copy2

    def copy_then_edit(source, destination):
        result = copy2(source, destination)
        target.write_text("independent change during snapshot")
        return result

    monkeypatch.setattr(backups.shutil, "copy2", copy_then_edit)
    record = backups.snapshot(target)
    assert record["backed_up"] is False
    assert backups.list_backups() == []
    assert not list(backups._root().iterdir())
    assert target.read_text() == "independent change during snapshot"


def test_snapshot_canonicalizes_existing_parent_alias(tmp_path):
    parent = tmp_path / "project"
    parent.mkdir()
    target = parent / "source.txt"
    target.write_text("original")
    alias = tmp_path / "alias"
    alias.symlink_to(parent, target_is_directory=True)
    record = backups.snapshot(alias / "source.txt")
    assert record["path"] == str(target.resolve())
    target.write_text("agent output")
    assert backups.record_completed_edit(record["id"], "agent output")
    backups.restore(record["id"])
    assert (alias / "source.txt").read_text() == "original"


def _two_completed_edits(tmp_path):
    target = tmp_path / "chain.txt"
    target.write_text("before")
    first = backups.snapshot(target)
    target.write_text("first agent edit")
    assert backups.record_completed_edit(first["id"], "first agent edit")
    second = backups.snapshot(target)
    target.write_text("second agent edit")
    assert backups.record_completed_edit(second["id"], "second agent edit")
    return target, first, second


def test_consecutive_agent_edits_can_be_undone_in_reverse_order(tmp_path):
    target, first, second = _two_completed_edits(tmp_path)
    backups.restore(second["id"])
    assert target.read_text() == "first agent edit"
    backups.restore(first["id"])
    assert target.read_text() == "before"


@pytest.mark.parametrize("recreated", [False, True])
def test_identical_agent_write_keeps_undo_chain_but_recreation_does_not(tmp_path: Path, recreated: bool) -> None:
    target = tmp_path / "chain.txt"
    target.write_text("before")
    first = backups.snapshot(target)
    target.write_text("agent edit")
    assert backups.record_completed_edit(first["id"], "agent edit")
    second = backups.snapshot(target)
    target.write_text("agent edit")
    assert backups.record_completed_edit(second["id"], "agent edit")
    if recreated:
        target.rename(tmp_path / "previous-file")
        target.write_text("agent edit")
    unchanged = target.stat()
    backups.restore(second["id"])
    assert target.stat() == unchanged
    if recreated:
        with pytest.raises(backups.RestoreConflict):
            backups.restore(first["id"])
        assert target.read_text() == "agent edit"
    else:
        backups.restore(first["id"])
        assert target.read_text() == "before"


def test_chained_undo_still_preserves_a_later_independent_edit(tmp_path):
    target, first, second = _two_completed_edits(tmp_path)
    backups.restore(second["id"])
    target.write_text("independent edit after undo")
    with pytest.raises(backups.RestoreConflict):
        backups.restore(first["id"])
    assert target.read_text() == "independent edit after undo"


def test_intervening_recreation_does_not_reauthorize_an_older_backup(tmp_path):
    target = tmp_path / "chain.txt"
    target.write_text("before")
    first = backups.snapshot(target)
    target.write_text("agent edit")
    assert backups.record_completed_edit(first["id"], "agent edit")
    target.rename(tmp_path / "previous-file")
    target.write_text("agent edit")
    second = backups.snapshot(target)
    target.write_text("second edit")
    assert backups.record_completed_edit(second["id"], "second edit")
    backups.restore(second["id"])
    with pytest.raises(backups.RestoreConflict):
        backups.restore(first["id"])
    assert target.read_text() == "agent edit"


def test_failed_chain_publication_preserves_older_conflict_guard(tmp_path, monkeypatch):
    target, first, second = _two_completed_edits(tmp_path)
    before = backups._manifest_path().read_bytes()
    def fail_write(records):
        raise OSError("injected publication failure")
    monkeypatch.setattr(backups, "_write_manifest", fail_write)
    result = backups.restore(second["id"])
    assert target.read_text() == "first agent edit"
    assert "confirmation" in result["note"]
    assert backups._manifest_path().read_bytes() == before
    with pytest.raises(backups.RestoreConflict):
        backups.restore(first["id"])


def test_three_consecutive_agent_edits_can_be_undone(tmp_path):
    target, first, second = _two_completed_edits(tmp_path)
    third = backups.snapshot(target)
    target.write_text("third edit")
    assert backups.record_completed_edit(third["id"], "third edit")
    for record, expected in [(third, "second agent edit"), (second, "first agent edit"), (first, "before")]:
        backups.restore(record["id"])
        assert target.read_text() == expected
