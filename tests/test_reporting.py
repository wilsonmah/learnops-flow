import csv
import io
from datetime import date

import pytest

from learning_ops.clock import utc
from learning_ops.reporting import Filters, export_csv, report, safe_cell


@pytest.fixture
def fixed_report(env):
    ids = []
    for _ in range(2):
        sid = env.session(capacity=5)
        ids.extend((sid, env.enrollment.register(sid, i)) for i in range(1, 5))
    cancelled = env.enrollment.register(ids[0][0], 5)
    env.enrollment.cancel(cancelled, "Fixture cancellation")
    cancelled_session = env.session()
    env.enrollment.register(cancelled_session, 6)
    env.schedule.cancel(cancelled_session, "Fixture cancelled session")
    future = env.session(
        capacity=4,
        start="2026-11-01T14:00:00Z",
        end="2026-11-01T16:00:00Z",
        due="2026-11-02T16:00:00Z",
    )
    for i in (1, 2):
        env.enrollment.register(future, i)
    env.clock.value = utc("2026-10-27T14:00:00Z")
    for index, (sid, eid) in enumerate(ids):
        env.completion.save_batch(
            sid,
            [
                {
                    "id": eid,
                    "attendance_status": "present"
                    if index < 6
                    else "absent"
                    if index == 6
                    else "unrecorded",
                    "completion_status": "completed" if index < 5 else "not_completed",
                }
            ],
        )
    return env, ids


def test_spec_fixed_fixture_exact_metrics(fixed_report):
    env, _ = fixed_report
    filters = Filters(date(2026, 10, 1), date(2026, 10, 31))
    data = report(env.settings, filters, env.clock)
    summary = data["summary"]
    for key, numerator, denominator, rate in (
        ("attendance", 6, 8, 0.75),
        ("completion", 5, 8, 0.625),
        ("overdue", 3, 8, 0.375),
        ("coverage", 7, 8, 0.875),
        ("capacity", 8, 10, 0.8),
    ):
        assert summary[key] == {"numerator": numerator, "denominator": denominator, "rate": rate}
    assert summary["registrations"] == 8
    assert summary["distinct_learners"] == 4
    assert summary["cancelled"] == 2
    assert summary["unrecorded"] == 1
    assert any(r["late_completion"] for r in data["rows"])
    whole = report(env.settings, Filters(date(2026, 10, 1), date(2026, 11, 30)), env.clock)
    assert whole["summary"]["registrations"] == 10
    assert whole["summary"]["capacity"]["rate"] == 10 / 14
    for key in ("attendance", "completion", "overdue", "coverage"):
        assert whole["summary"][key] == summary[key]


def test_excused_keeps_denominator_and_empty_is_na(fixed_report):
    env, ids = fixed_report
    sid, eid = ids[0]
    env.completion.save_batch(
        sid,
        [{"id": eid, "attendance_status": "excused", "completion_status": "not_completed"}],
        "Corrected fixture record",
    )
    summary = report(env.settings, Filters(date(2026, 10, 1), date(2026, 10, 31)), env.clock)[
        "summary"
    ]
    assert summary["attendance"]["numerator"] == 5
    assert summary["attendance"]["denominator"] == 8
    assert summary["completion"]["numerator"] == 4
    assert summary["excused"] == 1
    empty = report(env.settings, Filters(date(2020, 1, 1), date(2020, 1, 1)), env.clock)
    assert not empty["rows"]
    assert all(
        empty["summary"][key]["rate"] is None
        for key in ("attendance", "completion", "overdue", "coverage", "capacity")
    )


def test_department_snapshot_filter_and_csv_identical_rows(fixed_report):
    env, _ = fixed_report
    data = report(
        env.settings,
        Filters(date(2026, 10, 1), date(2026, 11, 30), department_id=1, course_id=env.course),
        env.clock,
    )
    assert data["summary"]["capacity"] is None
    assert data["sessions"] == []
    exported = list(csv.DictReader(io.StringIO(export_csv(data["rows"]).decode("utf-8-sig"))))
    assert [int(r["id"]) for r in exported] == [r["id"] for r in data["rows"]]
    assert all(r["data_source"] == "Synthetic data / Portfolio demo" for r in exported)


@pytest.mark.parametrize(
    "value", ["=SUM(A1)", "+1", "-2", "@formula", "  =1", "\tdata", "\rdata", "\ndata"]
)
def test_csv_formula_safety(value):
    assert safe_cell(value) == "'" + value
    csv_rows = list(
        csv.DictReader(io.StringIO(export_csv([{"display_name": value}]).decode("utf-8-sig")))
    )
    assert csv_rows[0]["display_name"] == "'" + value
    assert safe_cell("Normal value") == "Normal value"


def test_query_uses_local_day_inclusive_start_exclusive_end(env):
    env.session(
        start="2026-10-25T04:00:00Z", end="2026-10-25T05:00:00Z", due="2026-10-25T05:00:00Z"
    )
    env.session(
        start="2026-10-26T03:59:59Z", end="2026-10-26T05:00:00Z", due="2026-10-26T05:00:00Z"
    )
    env.session(
        start="2026-10-26T04:00:00Z", end="2026-10-26T05:00:00Z", due="2026-10-26T05:00:00Z"
    )
    data = report(env.settings, Filters(date(2026, 10, 25), date(2026, 10, 25)), env.clock)
    assert [s["session_id"] for s in data["sessions"]] == [1, 2]
