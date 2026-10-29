import sqlite3
from concurrent.futures import ThreadPoolExecutor
from dataclasses import replace
from datetime import date, datetime
from threading import Barrier

import pytest

from learning_ops.clock import date_bounds, local_to_utc, utc
from learning_ops.config import DomainError
from learning_ops.db import connect, initialize
from learning_ops.services.communications import Communications, MockProvider
from learning_ops.services.completion import Completion
from learning_ops.services.enrollment import Enrollment
from learning_ops.services.scheduling import Scheduling
from tests.conftest import rows


def test_registration_idempotency_and_capacity(env):
    sid = env.session(capacity=1)
    first = env.enrollment.register(sid, 1)
    assert env.enrollment.register(sid, 1) == first
    with pytest.raises(DomainError, match="full"):
        env.enrollment.register(sid, 2)
    assert len(rows(env, "enrollments")) == 1
    assert len(rows(env, "communication_jobs")) == 1


def test_two_independent_connections_compete_for_last_seat(env):
    sid = env.session(capacity=1)
    barrier = Barrier(2)

    def register(learner):
        barrier.wait()
        try:
            Enrollment(env.settings, env.clock).register(sid, learner)
            return "ok"
        except DomainError as exc:
            return str(exc)

    with ThreadPoolExecutor(max_workers=2) as pool:
        result = list(pool.map(register, [1, 2]))
    assert result.count("ok") == 1
    assert any("full" in r for r in result)
    assert len(rows(env, "enrollments")) == 1


@pytest.mark.parametrize(
    "state", ["draft", "cancelled", "started", "inactive_learner", "inactive_course"]
)
def test_invalid_registration_no_side_effects(env, state):
    sid = env.session(publish=state != "draft")
    if state == "cancelled":
        env.schedule.cancel(sid, "Demo cancellation")
    if state == "started":
        env.clock.value = utc("2026-10-25T14:00:00Z")
    if state.startswith("inactive"):
        with connect(env.settings, write=True) as conn:
            conn.execute(
                "UPDATE learners SET active=0 WHERE id=1"
                if state == "inactive_learner"
                else "UPDATE courses SET active=0"
            )
    before = rows(env, "audit_events")
    with pytest.raises(DomainError):
        env.enrollment.register(sid, 1)
    assert rows(env, "enrollments") == rows(env, "communication_jobs") == []
    assert rows(env, "audit_events") == before


def test_cancel_reregister_snapshot_and_session_cancel(env):
    sid = env.session(capacity=2)
    eid = env.enrollment.register(sid, 1)
    env.clock.value = utc("2026-10-24T14:00:00Z")
    assert env.comm.run_rules() == 1
    env.enrollment.cancel(eid, "Cannot attend")
    assert all(
        j["status"] == "cancelled"
        for j in rows(env, "communication_jobs")
        if j["message_type"] != "cancellation"
    )
    with connect(env.settings, write=True) as conn:
        conn.execute("UPDATE learners SET department_id=2 WHERE id=1")
    assert env.enrollment.register(sid, 1) == eid
    assert rows(env, "enrollments")[0]["registration_cycle"] == 2
    assert rows(env, "enrollments")[0]["department_id_at_registration"] == 2
    env.enrollment.register(sid, 2)
    env.schedule.cancel(sid, "Facilitator unavailable")
    assert all(
        e["status"] == "cancelled" and e["cancellation_reason"] == "session_cancelled"
        for e in rows(env, "enrollments")
    )
    assert (
        len([j for j in rows(env, "communication_jobs") if j["message_type"] == "cancellation"])
        == 3
    )
    assert any(
        '"department_id_at_registration": 1' in (a["before_json"] or "")
        for a in rows(env, "audit_events")
    )


def test_post_start_cancel_requires_explicit_audited_correction(env):
    sid = env.session()
    eid = env.enrollment.register(sid, 1)
    env.clock.value = utc("2026-10-25T14:00:00Z")
    with pytest.raises(DomainError, match="correction"):
        env.enrollment.cancel(eid, "Wrong learner")
    with pytest.raises(DomainError, match="Coordinator"):
        Enrollment(env.settings, env.clock, "Learner").cancel(eid, "Wrong learner", correction=True)
    env.enrollment.cancel(eid, "Wrong learner", correction=True)
    assert any(a["action"] == "registration_corrected" for a in rows(env, "audit_events"))


def test_publish_locks_fields_and_snapshots_rule(env):
    sid = env.session()
    env.schedule.save_course("Changed", "Core", "Demo", "attendance_only", course_id=env.course)
    assert rows(env, "sessions")[0]["completion_rule_snapshot"] == "attendance_plus_confirmation"
    data = {
        k: rows(env, "sessions")[0][k]
        for k in (
            "course_id",
            "facilitator_name",
            "delivery_mode",
            "location",
            "starts_at_utc",
            "ends_at_utc",
            "timezone",
            "capacity",
            "completion_due_at_utc",
        )
    }
    with pytest.raises(DomainError, match="locked"):
        env.schedule.save_draft(data, sid)
    env.enrollment.register(sid, 1)
    env.enrollment.register(sid, 2)
    with pytest.raises(DomainError):
        env.schedule.change_capacity(sid, 1, "Too low")
    env.schedule.change_capacity(sid, 2, "Match current roster")
    with pytest.raises(DomainError):
        env.schedule.close(sid)
    with pytest.raises(DomainError):
        env.schedule.delete_draft(sid)
    draft = env.session(publish=False)
    env.schedule.delete_draft(draft)
    env.clock.value = utc("2026-10-25T16:00:00Z")
    env.schedule.close(sid)
    assert rows(env, "sessions")[0]["status"] == "completed"


@pytest.mark.parametrize("rule", ["attendance_only", "attendance_plus_confirmation"])
def test_completion_rules_and_atomic_batch(env, rule):
    env.schedule.save_course("Demo", "Core", "Demo", rule, course_id=env.course)
    sid = env.session()
    ids = [env.enrollment.register(sid, i) for i in (1, 2)]
    valid = {"id": ids[0], "attendance_status": "present", "completion_status": "not_completed"}
    with pytest.raises(DomainError, match="after"):
        env.completion.save_batch(sid, [valid])
    env.clock.value = utc("2026-10-25T17:00:00Z")
    before = rows(env, "audit_events")
    with pytest.raises(DomainError, match="Row 2"):
        env.completion.save_batch(sid, [valid, {"id": ids[1], "attendance_status": "invalid"}])
    assert rows(env, "audit_events") == before
    assert all(e["attendance_status"] == "unrecorded" for e in rows(env, "enrollments"))
    env.completion.save_batch(sid, [valid])
    assert rows(env, "enrollments")[0]["completion_status"] == (
        "completed" if rule == "attendance_only" else "not_completed"
    )
    if rule == "attendance_plus_confirmation":
        with pytest.raises(DomainError, match="present"):
            env.completion.save_batch(
                sid,
                [{"id": ids[1], "attendance_status": "absent", "completion_status": "completed"}],
            )


def test_completion_revisions_times_and_sent_history(env):
    sid = env.session()
    eid = env.enrollment.register(sid, 1)
    env.clock.value = utc("2026-10-25T17:00:00Z")
    complete = {"id": eid, "attendance_status": "present", "completion_status": "completed"}
    for invalid in ("2026-10-25T15:00:00Z", "2026-10-25T18:00:00Z"):
        with pytest.raises(DomainError, match="Completion time"):
            env.completion.save_batch(sid, [{**complete, "completed_at": invalid}])
    env.completion.save_batch(sid, [complete])
    revoke = {**complete, "completion_status": "not_completed"}
    with pytest.raises(DomainError, match="reason"):
        env.completion.save_batch(sid, [revoke])
    env.completion.save_batch(sid, [revoke], "Needs confirmation")
    assert [j for j in rows(env, "communication_jobs") if j["message_type"] == "completion"][0][
        "status"
    ] == "cancelled"
    env.completion.save_batch(sid, [complete], "Confirmed")
    env.comm.process()
    env.completion.save_batch(sid, [revoke], "Correction")
    assert any(
        j["status"] == "simulated_sent"
        for j in rows(env, "communication_jobs")
        if j["message_type"] == "completion"
    )
    assert rows(env, "enrollments")[0]["completion_revision"] == 2


def test_rule_boundaries_stale_jobs_and_retry_limit(env):
    sid = env.session()
    eid = env.enrollment.register(sid, 1)
    env.clock.value = utc("2026-10-24T13:59:59Z")
    assert env.comm.run_rules() == 0
    env.clock.value = utc("2026-10-24T14:00:00Z")
    assert env.comm.run_rules() == 1
    assert env.comm.run_rules() == 0
    env.clock.value = utc("2026-10-25T14:00:00Z")
    result = env.comm.process(provider=MockProvider(3))
    assert result == {"cancelled": 1, "failed": 1, "simulated_sent": 0}
    env.comm.process(retry_failed=True, provider=MockProvider(3))
    env.comm.process(retry_failed=True, provider=MockProvider(3))
    assert env.comm.process(retry_failed=True)["simulated_sent"] == 0
    assert max(j["attempt_count"] for j in rows(env, "communication_jobs")) == 3
    env.clock.value = utc("2026-10-26T16:00:00Z")
    assert env.comm.run_rules() == 0
    env.clock.value = utc("2026-10-26T16:00:01Z")
    assert env.comm.run_rules() == 1
    env.completion.save_batch(
        sid, [{"id": eid, "attendance_status": "present", "completion_status": "completed"}]
    )
    assert (
        next(j for j in rows(env, "communication_jobs") if j["message_type"] == "followup")[
            "status"
        ]
        == "cancelled"
    )
    result = env.comm.process(provider=MockProvider(1))
    assert result["failed"] == 1
    assert env.comm.process(retry_failed=True, provider=MockProvider(1))["simulated_sent"] == 1
    snapshot = rows(env, "communication_jobs")
    env.comm.run_rules()
    env.comm.process()
    env.comm.process(retry_failed=True)
    assert rows(env, "communication_jobs") == snapshot


def test_unknown_template_rolls_back_enrollment_and_audit(env):
    sid = env.session()
    with connect(env.settings, write=True) as conn:
        conn.execute(
            "UPDATE message_templates SET body_template='{unknown}' WHERE message_type='confirmation'"
        )
    before = rows(env, "audit_events")
    with pytest.raises(DomainError, match="variable"):
        env.enrollment.register(sid, 1)
    assert not rows(env, "enrollments")
    assert not rows(env, "communication_jobs")
    assert rows(env, "audit_events") == before


def test_template_version_keeps_snapshot(env):
    sid = env.session()
    env.enrollment.register(sid, 1)
    old = rows(env, "communication_jobs")[0]
    env.comm.save_template(
        "confirmation", "New {course}", "Hi {learner} at {session_date} {timezone}"
    )
    env.enrollment.register(sid, 2)
    assert rows(env, "communication_jobs")[0] == old
    assert rows(env, "communication_jobs")[1]["subject_rendered"].startswith("New")
    with pytest.raises(DomainError):
        env.comm.save_template("confirmation", "{learner.__class__}", "Demo")


def test_database_constraints_and_migration_idempotence(env):
    initialize(env.settings)
    with connect(env.settings, write=True) as conn:
        assert conn.execute("PRAGMA foreign_keys").fetchone()[0] == 1
        assert conn.execute("SELECT count(*) FROM schema_migrations").fetchone()[0] == 1
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE learners SET department_id=999 WHERE id=1")
    sid = env.session()
    env.enrollment.register(sid, 1)
    with connect(env.settings, write=True) as conn:
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE sessions SET capacity=0")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE enrollments SET attendance_status='unknown'")
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute("UPDATE communication_jobs SET attempt_count=4")


def test_all_public_write_services_rejected(env):
    sid = env.session()
    eid = env.enrollment.register(sid, 1)
    public = replace(env.settings, app_mode="public_readonly")
    schedule, enroll, complete, comm = [
        cls(public, env.clock) for cls in (Scheduling, Enrollment, Completion, Communications)
    ]
    before = env.settings.database_path.read_bytes()
    calls = [
        lambda: initialize(public),
        lambda: schedule.save_course("X", "X", "X", "attendance_only"),
        lambda: schedule.save_draft({}),
        lambda: schedule.publish(sid),
        lambda: schedule.cancel(sid, "Demo"),
        lambda: schedule.close(sid),
        lambda: schedule.delete_draft(sid),
        lambda: schedule.change_capacity(sid, 10, "Demo"),
        lambda: enroll.register(sid, 2),
        lambda: enroll.cancel(eid, "Demo"),
        lambda: complete.save_batch(sid, []),
        lambda: comm.save_template("confirmation", "Hi", "Hi"),
        comm.run_rules,
        comm.process,
        lambda: comm.process(retry_failed=True),
    ]
    for call in calls:
        with pytest.raises(DomainError, match="read-only"):
            call()
    assert env.settings.database_path.read_bytes() == before


def test_dst_and_date_boundaries():
    with pytest.raises(DomainError, match="does not exist"):
        local_to_utc(datetime(2026, 3, 8, 2, 30), "America/Toronto")
    with pytest.raises(DomainError, match="Ambiguous"):
        local_to_utc(datetime(2026, 11, 1, 1, 30), "America/Toronto")
    first = local_to_utc(datetime(2026, 11, 1, 1, 30), "America/Toronto", 0)
    second = local_to_utc(datetime(2026, 11, 1, 1, 30), "America/Toronto", 1)
    assert (second - first).total_seconds() == 3600
    assert date_bounds(date(2026, 11, 1), date(2026, 11, 1), "America/Toronto") == (
        "2026-11-01T04:00:00Z",
        "2026-11-02T05:00:00Z",
    )
