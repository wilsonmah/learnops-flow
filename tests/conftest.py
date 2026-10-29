from types import SimpleNamespace

import pytest

from learning_ops.clock import FixedClock, stamp, utc
from learning_ops.config import Settings
from learning_ops.db import connect, initialize
from learning_ops.services.communications import Communications, install_templates
from learning_ops.services.completion import Completion
from learning_ops.services.enrollment import Enrollment
from learning_ops.services.scheduling import Scheduling


@pytest.fixture
def env(tmp_path):
    settings = Settings(tmp_path / "test.sqlite3", "local_demo")
    initialize(settings)
    clock = FixedClock(utc("2026-10-20T14:00:00Z"))
    with connect(settings, write=True) as conn:
        conn.executemany(
            "INSERT INTO departments VALUES (?,?)", [(1, "Support"), (2, "Engineering")]
        )
        for i in range(1, 21):
            conn.execute(
                "INSERT INTO learners (id,synthetic_employee_code,display_name,email,department_id,created_at) VALUES (?,?,?,?,?,?)",
                (
                    i,
                    f"SYN-{i}",
                    f"Demo {i}",
                    f"learner{i}@example.com",
                    1 if i <= 10 else 2,
                    stamp(clock.now()),
                ),
            )
        install_templates(conn)
    schedule = Scheduling(settings, clock)
    course = schedule.save_course(
        "Demo course", "Core", "Synthetic", "attendance_plus_confirmation"
    )
    result = SimpleNamespace(
        settings=settings,
        clock=clock,
        schedule=schedule,
        enrollment=Enrollment(settings, clock),
        completion=Completion(settings, clock),
        comm=Communications(settings, clock),
        course=course,
    )

    def session(
        capacity=5,
        start="2026-10-25T14:00:00Z",
        end="2026-10-25T16:00:00Z",
        due="2026-10-26T16:00:00Z",
        publish=True,
        course_id=None,
    ):
        sid = schedule.save_draft(
            {
                "course_id": course_id or course,
                "facilitator_name": "Demo facilitator",
                "delivery_mode": "online",
                "location": "https://example.com",
                "starts_at_utc": start,
                "ends_at_utc": end,
                "timezone": "America/Toronto",
                "capacity": capacity,
                "completion_due_at_utc": due,
            }
        )
        if publish:
            schedule.publish(sid)
        return sid

    result.session = session
    return result


def rows(env, table):
    with connect(env.settings) as conn:
        return [dict(r) for r in conn.execute(f"SELECT * FROM {table} ORDER BY id")]
