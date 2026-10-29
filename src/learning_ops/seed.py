import random
from datetime import UTC, date, datetime, timedelta

from learning_ops.clock import FixedClock, stamp
from learning_ops.config import DomainError
from learning_ops.db import connect
from learning_ops.services.base import audit
from learning_ops.services.communications import Communications, MockProvider, install_templates
from learning_ops.services.completion import Completion
from learning_ops.services.enrollment import Enrollment
from learning_ops.services.scheduling import Scheduling


def seed_demo(settings, seed=42, base_date=date(2026, 10, 25)):
    """Deterministic synthetic history, built through the same business services."""
    settings.require_write()
    base = datetime.combine(base_date, datetime.min.time(), UTC).replace(hour=14)
    clock = FixedClock(base - timedelta(days=100))
    rng = random.Random(seed)
    with connect(settings, write=True) as conn:
        if any(
            conn.execute(f"SELECT 1 FROM {table} LIMIT 1").fetchone()
            for table in ("learners", "courses", "sessions", "message_templates", "demo_metadata")
        ):
            raise DomainError(
                "Database already contains data. Use scripts.reset_demo --confirm-reset after stopping the app, or choose a fresh DATABASE_PATH."
            )
        for i, name in enumerate(
            ("Customer Success", "People Operations", "Product", "Finance", "Engineering", "Sales"),
            1,
        ):
            conn.execute("INSERT INTO departments VALUES (?,?)", (i, name))
        for i in range(1, 201):
            conn.execute(
                "INSERT INTO learners (id,synthetic_employee_code,display_name,email,department_id,created_at) VALUES (?,?,?,?,?,?)",
                (
                    i,
                    f"SYN-{i:04}",
                    f"Demo Learner {i:03}",
                    f"learner{i:03}@example.com",
                    (i - 1) % 6 + 1,
                    stamp(clock.now()),
                ),
            )
        install_templates(conn)
        conn.executemany(
            "INSERT INTO demo_metadata VALUES (?,?)",
            [
                ("seed", str(seed)),
                ("base_date", base_date.isoformat()),
                ("default_as_of", stamp(base)),
                ("source", "Synthetic data / Portfolio demo"),
            ],
        )
        audit(
            conn,
            clock,
            "Seed generator",
            "learners",
            0,
            "synthetic_seed",
            after={"learners": 200, "departments": 6, "seed": seed},
        )
    scheduling, enrollment, completion = (
        Scheduling(settings, clock),
        Enrollment(settings, clock),
        Completion(settings, clock),
    )
    names = (
        "Customer Support Onboarding",
        "Facilitation Essentials",
        "Data Literacy",
        "Feedback Conversations",
        "Project Coordination",
        "Inclusive Meetings",
        "Knowledge Sharing",
        "Operational Reporting",
    )
    course_ids = [
        scheduling.save_course(
            name,
            "Core skills" if i < 4 else "Development",
            "Fictional training for a synthetic portfolio demo.",
            "attendance_only" if i % 2 == 0 else "attendance_plus_confirmation",
        )
        for i, name in enumerate(names)
    ]
    for i in range(24):
        start = base + timedelta(days=(i - 12) * 5)
        clock.value = min(start - timedelta(days=2), base - timedelta(days=1))
        session_id = scheduling.save_draft(
            {
                "course_id": course_ids[i % 8],
                "facilitator_name": f"Demo Facilitator {i % 4 + 1}",
                "delivery_mode": "online",
                "location": "https://example.com/training",
                "starts_at_utc": start,
                "ends_at_utc": start + timedelta(hours=2),
                "timezone": "America/Toronto",
                "capacity": 17 if i % 5 == 0 else 22,
                "completion_due_at_utc": start + timedelta(days=2),
            }
        )
        scheduling.publish(session_id)
        ids = [
            enrollment.register(session_id, learner) for learner in rng.sample(range(1, 201), 17)
        ]
        if i == 22:
            scheduling.cancel(session_id, "Synthetic cancellation scenario")
        elif i == 23:
            enrollment.cancel(ids[0], "Synthetic learner cancellation")
        elif start + timedelta(days=3) < base:
            clock.value = start + timedelta(days=3 if i % 3 == 0 else 1)
            updates = []
            for j, entity_id in enumerate(ids):
                attendance = ("present", "present", "present", "absent", "excused", "unrecorded")[
                    j % 6
                ]
                updates.append(
                    {
                        "id": entity_id,
                        "attendance_status": attendance,
                        "completion_status": "completed"
                        if attendance == "present" and j % 3 != 2
                        else "not_completed",
                    }
                )
            completion.save_batch(session_id, updates)
            if i % 2 == 0:
                scheduling.close(session_id)
    clock.value = base
    communications = Communications(settings, clock)
    communications.run_rules()
    with connect(settings) as conn:
        job_ids = [r[0] for r in conn.execute("SELECT id FROM communication_jobs")]
    communications.process(provider=MockProvider(1, [i for i in job_ids if i % 3 == 0]))
    communications.process(
        retry_failed=True, provider=MockProvider(3, [i for i in job_ids if i % 6 == 0])
    )
    # Leave both recoverable failures and successful retries visible.
    with connect(settings, write=True) as conn:
        audit(
            conn,
            clock,
            "Seed generator",
            "learners",
            0,
            "seed_complete",
            after={"sessions": 24, "enrollments": 408},
        )
    return {"learners": 200, "departments": 6, "courses": 8, "sessions": 24, "enrollments": 408}
