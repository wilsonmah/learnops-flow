import json

from learning_ops.clock import SystemClock, stamp
from learning_ops.config import DomainError


def get(conn, table, entity_id):
    allowed = {
        "courses",
        "sessions",
        "enrollments",
        "learners",
        "communication_jobs",
        "message_templates",
    }
    if table not in allowed:
        raise ValueError("Unsupported entity")
    row = conn.execute(f"SELECT * FROM {table} WHERE id=?", (entity_id,)).fetchone()
    if row is None:
        raise DomainError(f"{table}: record {entity_id} was not found.")
    return dict(row)


def audit(conn, clock, actor, table, entity_id, action, before=None, after=None, reason=None):
    conn.execute(
        "INSERT INTO audit_events (actor_demo_role,entity_type,entity_id,action,before_json,after_json,reason,occurred_at_utc,business_as_of_utc) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            actor,
            table,
            entity_id,
            action,
            json.dumps(before) if before is not None else None,
            json.dumps(after) if after is not None else None,
            reason,
            stamp(SystemClock().now()),
            stamp(clock.now()),
        ),
    )


def record(conn, clock, actor, table, entity_id, action, before=None, reason=None):
    audit(conn, clock, actor, table, entity_id, action, before, get(conn, table, entity_id), reason)


class Service:
    def __init__(self, settings, clock=None, actor="Coordinator"):
        self.settings = settings
        self.clock = clock or SystemClock()
        self.actor = actor

    @property
    def now(self):
        return stamp(self.clock.now())
