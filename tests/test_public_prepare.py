from datetime import date

import pytest

from learning_ops.config import Settings
from learning_ops.db import connect
from scripts.prepare_public_demo import prepare


def test_public_preparation_is_rebuildable_and_never_overwrites(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_MODE", "local_demo")
    first, second = tmp_path / "public-a.sqlite3", tmp_path / "public-b.sqlite3"
    for path in (first, second):
        assert prepare(path, 42, date(2026, 10, 25))["learners"] == 200
    with connect(Settings(first)) as one, connect(Settings(second)) as two:
        for table in ("learners", "courses", "sessions", "enrollments", "communication_jobs"):
            assert [tuple(row) for row in one.execute(f"SELECT * FROM {table} ORDER BY id")] == [
                tuple(row) for row in two.execute(f"SELECT * FROM {table} ORDER BY id")
            ]
    before = first.read_bytes()
    with pytest.raises(FileExistsError):
        prepare(first, 42, date(2026, 10, 25))
    assert first.read_bytes() == before
    monkeypatch.setenv("APP_MODE", "public_readonly")
    with pytest.raises(ValueError, match="read-only"):
        prepare(tmp_path / "forbidden.sqlite3", 42, date(2026, 10, 25))
