from learning_ops.config import DomainError
from learning_ops.db import connect
from learning_ops.services.base import Service, get, record
from learning_ops.services.communications import cancel_jobs, enqueue


class Enrollment(Service):
    def register(self, session_id, learner_id):
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            learner = get(conn, "learners", learner_id)
            c = get(conn, "courses", s["course_id"])
            if (
                s["status"] != "scheduled"
                or self.now >= s["starts_at_utc"]
                or not learner["active"]
                or not c["active"]
            ):
                raise DomainError(
                    "Registration requires an active learner, active course and future scheduled session."
                )
            old = conn.execute(
                "SELECT * FROM enrollments WHERE session_id=? AND learner_id=?",
                (session_id, learner_id),
            ).fetchone()
            if old and old["status"] == "registered":
                return old["id"]
            count = conn.execute(
                "SELECT count(*) FROM enrollments WHERE session_id=? AND status='registered'",
                (session_id,),
            ).fetchone()[0]
            if count >= s["capacity"]:
                raise DomainError("This session is full. Choose another session.")
            if old:
                entity_id = old["id"]
                cancel_jobs(
                    conn, self.clock, self.actor, entity_id, "Superseded by re-registration"
                )
                conn.execute(
                    "UPDATE enrollments SET status='registered',registration_cycle=registration_cycle+1,department_id_at_registration=?,registered_at=?,cancelled_at=NULL,cancellation_reason=NULL,attendance_status='unrecorded',completion_status='not_completed',completed_at=NULL,updated_at=? WHERE id=?",
                    (learner["department_id"], self.now, self.now, entity_id),
                )
            else:
                entity_id = conn.execute(
                    "INSERT INTO enrollments (learner_id,session_id,department_id_at_registration,status,registered_at,updated_at) VALUES (?,?,?,'registered',?,?)",
                    (learner_id, session_id, learner["department_id"], self.now, self.now),
                ).lastrowid
            record(
                conn,
                self.clock,
                self.actor,
                "enrollments",
                entity_id,
                "registered",
                dict(old) if old else None,
            )
            enqueue(conn, self.clock, self.actor, entity_id, "confirmation")
            return entity_id

    def cancel(self, enrollment_id, reason, *, correction=False):
        self.settings.require_write()
        if not reason.strip():
            raise DomainError("A cancellation or correction reason is required.")
        if correction and self.actor != "Coordinator":
            raise DomainError("A post-start correction requires the Coordinator demo role.")
        with connect(self.settings, write=True) as conn:
            e = get(conn, "enrollments", enrollment_id)
            s = get(conn, "sessions", e["session_id"])
            if e["status"] == "cancelled":
                return
            if self.now >= s["starts_at_utc"] and not correction:
                raise DomainError(
                    "Registration has started. Use the explicit Coordinator correction process for erroneous records."
                )
            reason = (
                "audited_correction: " if correction else "learner_cancelled: "
            ) + reason.strip()
            conn.execute(
                "UPDATE enrollments SET status='cancelled',cancelled_at=?,cancellation_reason=?,updated_at=? WHERE id=?",
                (self.now, reason, self.now, enrollment_id),
            )
            record(
                conn,
                self.clock,
                self.actor,
                "enrollments",
                enrollment_id,
                "registration_corrected" if correction else "cancelled",
                e,
                reason,
            )
            cancel_jobs(conn, self.clock, self.actor, enrollment_id, reason)
            enqueue(conn, self.clock, self.actor, enrollment_id, "cancellation", reason)
