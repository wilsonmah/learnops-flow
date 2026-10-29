from dataclasses import replace
from datetime import date

import pytest

from learning_ops.config import DomainError, Settings
from learning_ops.db import connect, initialize
from learning_ops.seed import seed_demo


def logical_snapshot(settings):
    with connect(settings) as conn:
        return {
            table: [tuple(row) for row in conn.execute(f"SELECT * FROM {table} ORDER BY id")]
            for table in (
                "departments",
                "learners",
                "courses",
                "sessions",
                "enrollments",
                "message_templates",
                "communication_jobs",
            )
        }


def test_seed_is_reproducible_constrained_and_refuses_overwrite(tmp_path):
    first = Settings(tmp_path / "first.sqlite3", "local_demo")
    second = replace(first, database_path=tmp_path / "second.sqlite3")
    for settings in (first, second):
        initialize(settings)
        assert seed_demo(settings, 42, date(2026, 10, 25)) == {
            "learners": 200,
            "departments": 6,
            "courses": 8,
            "sessions": 24,
            "enrollments": 408,
        }
        with connect(settings) as conn:
            assert not conn.execute("PRAGMA foreign_key_check").fetchall()
            assert conn.execute("PRAGMA integrity_check").fetchone()[0] == "ok"
            assert not conn.execute(
                "SELECT s.id FROM sessions s JOIN enrollments e ON e.session_id=s.id AND e.status='registered' GROUP BY s.id HAVING count(*)>s.capacity"
            ).fetchall()
            assert not conn.execute(
                "SELECT id FROM enrollments WHERE registered_at>'2026-10-25T14:00:00Z'"
            ).fetchall()
            assert (
                conn.execute(
                    "SELECT count(*) FROM communication_jobs WHERE status='failed' AND attempt_count=2"
                ).fetchone()[0]
                > 0
            )
            assert (
                conn.execute(
                    "SELECT count(*) FROM communication_jobs WHERE status='simulated_sent' AND attempt_count=2"
                ).fetchone()[0]
                > 0
            )
    assert logical_snapshot(first) == logical_snapshot(second)
    before = first.database_path.read_bytes()
    with pytest.raises(DomainError, match="already contains"):
        seed_demo(first, 42, date(2026, 10, 25))
    assert first.database_path.read_bytes() == before
    with pytest.raises(DomainError, match="read-only"):
        seed_demo(replace(first, app_mode="public_readonly"))
