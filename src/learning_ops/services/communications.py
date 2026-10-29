from datetime import timedelta
from string import Formatter
from zoneinfo import ZoneInfo

from learning_ops.clock import stamp, utc
from learning_ops.config import DomainError
from learning_ops.db import connect
from learning_ops.services.base import Service, get, record

TYPES = ("confirmation", "reminder", "cancellation", "completion", "followup")
VARIABLES = {"learner", "course", "session_date", "timezone", "reason"}


def validate_template(subject, body):
    for text in (subject, body):
        render(text, dict.fromkeys(VARIABLES, "Preview"))
    fields = {
        field for text in (subject, body) for _, field, _, _ in Formatter().parse(text) if field
    }
    missing = (VARIABLES - {"reason"}) - fields
    if missing:
        raise DomainError("Template is missing required variables: " + ", ".join(sorted(missing)))


def render(template, values):
    try:
        for _, field, spec, conversion in Formatter().parse(template):
            if field is not None and (field not in VARIABLES or spec or conversion):
                raise DomainError(f"Unsupported template variable: {field}")
        return template.format_map(values)
    except (KeyError, ValueError) as exc:
        raise DomainError(f"Invalid message template: {exc}") from exc


def install_templates(conn):
    for kind in TYPES:
        conn.execute(
            "INSERT INTO message_templates (message_type,version,subject_template,body_template) VALUES (?,1,?,?)",
            (
                kind,
                f"Training {kind}: {{course}}",
                "Hello {learner},\nYour training: {course}\nWhen: {session_date} ({timezone})\n"
                f"Update: {kind}. {{reason}}\nSynthetic data / Portfolio demo. Simulated delivery only.",
            ),
        )


def enqueue(conn, clock, actor, enrollment_id, kind, reason=""):
    e = get(conn, "enrollments", enrollment_id)
    s = get(conn, "sessions", e["session_id"])
    learner = get(conn, "learners", e["learner_id"])
    course = get(conn, "courses", s["course_id"])
    key = f"{e['id']}:{e['registration_cycle']}:{kind}"
    if kind == "completion":
        key += f":{e['completion_revision']}"
    if conn.execute("SELECT 1 FROM communication_jobs WHERE idempotency_key=?", (key,)).fetchone():
        return False
    template = conn.execute(
        "SELECT * FROM message_templates WHERE message_type=? AND active=1", (kind,)
    ).fetchone()
    if not template:
        raise DomainError(f"No active template for {kind}; initialize synthetic demo templates.")
    validate_template(template["subject_template"], template["body_template"])
    values = {
        "learner": learner["display_name"],
        "course": course["title"],
        "session_date": utc(s["starts_at_utc"]).astimezone(ZoneInfo(s["timezone"])).isoformat(),
        "timezone": s["timezone"],
        "reason": reason,
    }
    now = stamp(clock.now())
    job_id = conn.execute(
        "INSERT INTO communication_jobs (enrollment_id,registration_cycle,completion_revision,message_type,template_id,idempotency_key,recipient_snapshot,subject_rendered,body_rendered,due_at_utc,created_at) VALUES (?,?,?,?,?,?,?,?,?,?,?)",
        (
            e["id"],
            e["registration_cycle"],
            e["completion_revision"],
            kind,
            template["id"],
            key,
            learner["email"],
            render(template["subject_template"], values),
            render(template["body_template"], values),
            now,
            now,
        ),
    ).lastrowid
    record(conn, clock, actor, "communication_jobs", job_id, "queued")
    return True


def cancel_jobs(conn, clock, actor, enrollment_id, reason, kinds=None):
    jobs = conn.execute(
        "SELECT * FROM communication_jobs WHERE enrollment_id=? AND status IN ('pending','failed')",
        (enrollment_id,),
    ).fetchall()
    for job in jobs:
        if kinds is None or job["message_type"] in kinds:
            cancel_job(conn, clock, actor, dict(job), reason)


def cancel_job(conn, clock, actor, job, reason):
    conn.execute(
        "UPDATE communication_jobs SET status='cancelled',cancellation_reason=?,processed_at=? WHERE id=?",
        (reason, stamp(clock.now()), job["id"]),
    )
    record(conn, clock, actor, "communication_jobs", job["id"], "cancelled", job, reason)


class MockProvider:
    """Deterministic, network-free failure injection for each message attempt."""

    def __init__(self, fail_first=0, fail_job_ids=None):
        if fail_first not in (0, 1, 2, 3):
            raise DomainError("Mock failure count must be 0–3.")
        self.fail_first = fail_first
        self.fail_job_ids = None if fail_job_ids is None else frozenset(fail_job_ids)

    def deliver(self, job, attempt):
        if attempt <= self.fail_first and (
            self.fail_job_ids is None or job["id"] in self.fail_job_ids
        ):
            raise RuntimeError(f"Injected mock failure at attempt {attempt}.")


class Communications(Service):
    def save_template(self, kind, subject, body):
        self.settings.require_write()
        if kind not in TYPES or not subject.strip() or not body.strip():
            raise DomainError("Choose a message type and supply subject and body.")
        validate_template(subject, body)
        with connect(self.settings, write=True) as conn:
            old = conn.execute(
                "SELECT * FROM message_templates WHERE message_type=? AND active=1", (kind,)
            ).fetchone()
            version = conn.execute(
                "SELECT COALESCE(MAX(version),0)+1 FROM message_templates WHERE message_type=?",
                (kind,),
            ).fetchone()[0]
            if old:
                conn.execute("UPDATE message_templates SET active=0 WHERE id=?", (old["id"],))
                record(
                    conn,
                    self.clock,
                    self.actor,
                    "message_templates",
                    old["id"],
                    "retired",
                    dict(old),
                )
            entity_id = conn.execute(
                "INSERT INTO message_templates (message_type,version,subject_template,body_template) VALUES (?,?,?,?)",
                (kind, version, subject, body),
            ).lastrowid
            record(conn, self.clock, self.actor, "message_templates", entity_id, "created")
            return entity_id

    def run_rules(self):
        with connect(self.settings, write=True) as conn:
            rows = conn.execute(
                "SELECT e.*, s.starts_at_utc,s.ends_at_utc,s.completion_due_at_utc FROM enrollments e JOIN sessions s ON s.id=e.session_id WHERE e.status='registered' AND s.status IN ('scheduled','completed')"
            ).fetchall()
            count = 0
            now = self.clock.now()
            for e in rows:
                start = utc(e["starts_at_utc"])
                if start - timedelta(hours=24) <= now < start:
                    count += enqueue(conn, self.clock, self.actor, e["id"], "reminder")
                if (
                    utc(e["completion_due_at_utc"]) < now
                    and e["completion_status"] == "not_completed"
                ):
                    count += enqueue(conn, self.clock, self.actor, e["id"], "followup")
            return count

    def _invalid_reason(self, conn, job):
        e = get(conn, "enrollments", job["enrollment_id"])
        s = get(conn, "sessions", e["session_id"])
        if e["registration_cycle"] != job["registration_cycle"]:
            return "Superseded registration cycle"
        kind = job["message_type"]
        if kind == "cancellation":
            return None if e["status"] == "cancelled" else "Registration is active again"
        if e["status"] != "registered" or s["status"] == "cancelled":
            return "Enrollment or session cancelled"
        if kind == "reminder" and self.now >= s["starts_at_utc"]:
            return "Reminder expired at session start"
        if kind == "completion" and (
            e["completion_status"] != "completed"
            or e["completion_revision"] != job["completion_revision"]
        ):
            return "Completion revoked or superseded"
        if kind == "followup" and (
            e["completion_status"] == "completed" or self.now <= s["completion_due_at_utc"]
        ):
            return "Follow-up no longer applicable"
        return None

    def process(self, *, retry_failed=False, provider=None):
        provider = provider or MockProvider()
        if type(provider) is not MockProvider:
            raise DomainError("Only the built-in mock provider is permitted.")
        with connect(self.settings, write=True) as conn:
            state = "failed" if retry_failed else "pending"
            jobs = conn.execute(
                "SELECT * FROM communication_jobs WHERE status=? AND attempt_count<3 AND due_at_utc<=? ORDER BY id",
                (state, self.now),
            ).fetchall()
            result = {"simulated_sent": 0, "failed": 0, "cancelled": 0}
            for row in jobs:
                job = dict(row)
                reason = self._invalid_reason(conn, job)
                if reason:
                    cancel_job(conn, self.clock, self.actor, job, reason)
                    result["cancelled"] += 1
                    continue
                attempt = job["attempt_count"] + 1
                status, error = "simulated_sent", None
                try:
                    provider.deliver(job, attempt)
                except RuntimeError as exc:
                    status, error = "failed", str(exc)
                conn.execute(
                    "UPDATE communication_jobs SET status=?,attempt_count=?,last_error=?,processed_at=? WHERE id=?",
                    (status, attempt, error, self.now, job["id"]),
                )
                record(
                    conn,
                    self.clock,
                    self.actor,
                    "communication_jobs",
                    job["id"],
                    status,
                    job,
                    error,
                )
                result[status] += 1
            return result
