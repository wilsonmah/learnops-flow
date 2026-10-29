from zoneinfo import ZoneInfo

from learning_ops.clock import stamp
from learning_ops.config import DomainError
from learning_ops.db import connect
from learning_ops.services.base import Service, audit, get, record
from learning_ops.services.communications import cancel_jobs, enqueue

RULES = {"attendance_only", "attendance_plus_confirmation"}
SESSION_FIELDS = (
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


class Scheduling(Service):
    def save_course(
        self, title, category, description, completion_rule, active=True, course_id=None
    ):
        self.settings.require_write()
        if not title.strip() or completion_rule not in RULES:
            raise DomainError("A course needs a title and a valid completion rule.")
        with connect(self.settings, write=True) as conn:
            before = get(conn, "courses", course_id) if course_id else None
            values = (
                title.strip(),
                category.strip(),
                description.strip(),
                completion_rule,
                int(active),
            )
            if course_id:
                conn.execute(
                    "UPDATE courses SET title=?,category=?,description=?,completion_rule=?,active=? WHERE id=?",
                    (*values, course_id),
                )
            else:
                course_id = conn.execute(
                    "INSERT INTO courses (title,category,description,completion_rule,active,created_at) VALUES (?,?,?,?,?,?)",
                    (*values, self.now),
                ).lastrowid
            record(conn, self.clock, self.actor, "courses", course_id, "saved", before)
            return course_id

    def _validate_session(self, conn, data):
        if set(data) != set(SESSION_FIELDS):
            raise DomainError("Supply all draft session fields.")
        data = dict(data)
        for field in ("starts_at_utc", "ends_at_utc", "completion_due_at_utc"):
            data[field] = stamp(data[field])
        if not data["starts_at_utc"] < data["ends_at_utc"] <= data["completion_due_at_utc"]:
            raise DomainError("End must be after start; completion due must be at or after end.")
        if type(data["capacity"]) is not int or data["capacity"] <= 0:
            raise DomainError("Capacity must be a positive integer.")
        if data["delivery_mode"] not in {"online", "in_person"}:
            raise DomainError("Choose online or in_person.")
        if not data["facilitator_name"].strip() or not data["location"].strip():
            raise DomainError("Facilitator and fictitious location are required.")
        ZoneInfo(data["timezone"])
        get(conn, "courses", data["course_id"])
        return data

    def save_draft(self, data, session_id=None):
        with connect(self.settings, write=True) as conn:
            data = self._validate_session(conn, data)
            before = get(conn, "sessions", session_id) if session_id else None
            if before and before["status"] != "draft":
                raise DomainError(
                    "Published session details are locked; cancel and create a replacement."
                )
            values = [data[key] for key in SESSION_FIELDS]
            if session_id:
                conn.execute(
                    f"UPDATE sessions SET {','.join(f'{key}=?' for key in SESSION_FIELDS)},updated_at=? WHERE id=?",
                    (*values, self.now, session_id),
                )
            else:
                session_id = conn.execute(
                    f"INSERT INTO sessions ({','.join(SESSION_FIELDS)},created_at,updated_at) VALUES ({','.join('?' for _ in SESSION_FIELDS)},?,?)",
                    (*values, self.now, self.now),
                ).lastrowid
            record(conn, self.clock, self.actor, "sessions", session_id, "draft_saved", before)
            return session_id

    def publish(self, session_id):
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            c = get(conn, "courses", s["course_id"])
            if s["status"] != "draft" or s["starts_at_utc"] <= self.now or not c["active"]:
                raise DomainError("Publish an active course's draft with a future start time.")
            conn.execute(
                "UPDATE sessions SET status='scheduled',completion_rule_snapshot=?,updated_at=? WHERE id=?",
                (c["completion_rule"], self.now, session_id),
            )
            record(conn, self.clock, self.actor, "sessions", session_id, "published", s)

    def change_capacity(self, session_id, capacity, reason):
        self.settings.require_write()
        if type(capacity) is not int or capacity <= 0 or not reason.strip():
            raise DomainError("A positive integer capacity and reason are required.")
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            count = conn.execute(
                "SELECT count(*) FROM enrollments WHERE session_id=? AND status='registered'",
                (session_id,),
            ).fetchone()[0]
            if s["status"] not in {"draft", "scheduled"} or capacity < count:
                raise DomainError(
                    "Capacity cannot be below active registrations; session must be draft or scheduled."
                )
            conn.execute(
                "UPDATE sessions SET capacity=?,updated_at=? WHERE id=?",
                (capacity, self.now, session_id),
            )
            record(
                conn, self.clock, self.actor, "sessions", session_id, "capacity_changed", s, reason
            )

    def close(self, session_id):
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            if s["status"] != "scheduled" or s["ends_at_utc"] > self.now:
                raise DomainError("Only an ended scheduled session can be closed.")
            conn.execute(
                "UPDATE sessions SET status='completed',updated_at=? WHERE id=?",
                (self.now, session_id),
            )
            record(conn, self.clock, self.actor, "sessions", session_id, "closed", s)

    def cancel(self, session_id, reason):
        self.settings.require_write()
        if not reason.strip():
            raise DomainError("A cancellation reason is required.")
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            if s["status"] not in {"draft", "scheduled"}:
                raise DomainError("Only draft or scheduled sessions can be cancelled.")
            conn.execute(
                "UPDATE sessions SET status='cancelled',updated_at=? WHERE id=?",
                (self.now, session_id),
            )
            record(conn, self.clock, self.actor, "sessions", session_id, "cancelled", s, reason)
            for row in conn.execute(
                "SELECT * FROM enrollments WHERE session_id=? AND status='registered'",
                (session_id,),
            ).fetchall():
                e = dict(row)
                conn.execute(
                    "UPDATE enrollments SET status='cancelled',cancelled_at=?,cancellation_reason='session_cancelled',updated_at=? WHERE id=?",
                    (self.now, self.now, e["id"]),
                )
                record(
                    conn,
                    self.clock,
                    self.actor,
                    "enrollments",
                    e["id"],
                    "cancelled",
                    e,
                    "session_cancelled: " + reason,
                )
                cancel_jobs(conn, self.clock, self.actor, e["id"], "session_cancelled")
                enqueue(
                    conn,
                    self.clock,
                    self.actor,
                    e["id"],
                    "cancellation",
                    "Session cancelled: " + reason,
                )

    def delete_draft(self, session_id):
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            if (
                s["status"] != "draft"
                or conn.execute(
                    "SELECT 1 FROM enrollments WHERE session_id=?", (session_id,)
                ).fetchone()
            ):
                raise DomainError("Only drafts without any enrollment history can be deleted.")
            conn.execute("DELETE FROM sessions WHERE id=?", (session_id,))
            audit(conn, self.clock, self.actor, "sessions", session_id, "deleted", s)
