from learning_ops.clock import stamp
from learning_ops.config import DomainError
from learning_ops.db import connect
from learning_ops.services.base import Service, get, record
from learning_ops.services.communications import cancel_jobs, enqueue


class Completion(Service):
    def save_batch(self, session_id, rows, reason=""):
        with connect(self.settings, write=True) as conn:
            s = get(conn, "sessions", session_id)
            if s["status"] not in {"scheduled", "completed"} or self.now < s["ends_at_utc"]:
                raise DomainError(
                    "Attendance and completion can be recorded only after a non-cancelled session ends."
                )
            seen = set()
            for index, row in enumerate(rows, 1):
                try:
                    self._save(conn, s, row, reason, seen)
                except (DomainError, KeyError, ValueError) as exc:
                    raise DomainError(f"Row {index}: {exc}") from exc

    def _save(self, conn, session, row, reason, seen):
        e = get(conn, "enrollments", row["id"])
        if e["id"] in seen:
            raise DomainError("Enrollment appears twice in this batch.")
        seen.add(e["id"])
        if e["session_id"] != session["id"] or e["status"] != "registered":
            raise DomainError("Enrollment must be active and belong to the selected session.")
        attendance = row["attendance_status"]
        if attendance not in {"unrecorded", "present", "absent", "excused"}:
            raise DomainError("Choose unrecorded, present, absent or excused.")
        complete = row.get("completion_status", "not_completed")
        if complete not in {"not_completed", "completed"}:
            raise DomainError("Invalid completion status.")
        if session["completion_rule_snapshot"] == "attendance_only":
            complete = "completed" if attendance == "present" else "not_completed"
        if complete == "completed" and attendance != "present":
            raise DomainError("Only a present learner can be completed.")
        completed_at = None
        if complete == "completed":
            completed_at = stamp(row.get("completed_at") or e["completed_at"] or self.now)
            if not session["ends_at_utc"] <= completed_at <= self.now:
                raise DomainError(
                    "Completion time must be between session end and the business clock."
                )
        if (attendance, complete, completed_at) == (
            e["attendance_status"],
            e["completion_status"],
            e["completed_at"],
        ):
            return
        if (
            e["attendance_status"] != "unrecorded" or e["completion_status"] == "completed"
        ) and not reason.strip():
            raise DomainError(
                "A reason is required to change an existing attendance or completion record."
            )
        newly_completed = complete == "completed" and e["completion_status"] != "completed"
        conn.execute(
            "UPDATE enrollments SET attendance_status=?,completion_status=?,completed_at=?,completion_revision=completion_revision+?,updated_at=? WHERE id=?",
            (attendance, complete, completed_at, int(newly_completed), self.now, e["id"]),
        )
        record(
            conn,
            self.clock,
            self.actor,
            "enrollments",
            e["id"],
            "attendance_completion_saved",
            e,
            reason or "Initial recording",
        )
        if complete != "completed":
            cancel_jobs(conn, self.clock, self.actor, e["id"], "Completion revoked", {"completion"})
        else:
            cancel_jobs(conn, self.clock, self.actor, e["id"], "Learner completed", {"followup"})
        if newly_completed:
            enqueue(conn, self.clock, self.actor, e["id"], "completion")
