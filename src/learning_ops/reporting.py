import csv
import io
from dataclasses import dataclass
from datetime import date
from zoneinfo import ZoneInfo

from learning_ops.clock import date_bounds, stamp, utc
from learning_ops.db import connect


@dataclass(frozen=True)
class Filters:
    start: date
    end: date
    timezone: str = "America/Toronto"
    course_id: int | None = None
    department_id: int | None = None


def fraction(numerator, denominator):
    return {
        "numerator": numerator,
        "denominator": denominator,
        "rate": numerator / denominator if denominator else None,
    }


def metrics(rows, as_of):
    active = [
        r
        for r in rows
        if r["status"] == "registered" and r["session_status"] in {"scheduled", "completed"}
    ]
    ended = [r for r in active if r["ends_at_utc"] <= as_of]
    due = [r for r in ended if r["completion_due_at_utc"] < as_of]
    return {
        "registrations": len(active),
        "distinct_learners": len({r["learner_id"] for r in active}),
        "cancelled": sum(r["status"] == "cancelled" for r in rows),
        "attendance": fraction(sum(r["attendance_status"] == "present" for r in ended), len(ended)),
        "completion": fraction(
            sum(r["completion_status"] == "completed" for r in ended), len(ended)
        ),
        "overdue": fraction(sum(r["completion_status"] != "completed" for r in due), len(due)),
        "coverage": fraction(
            sum(r["attendance_status"] != "unrecorded" for r in ended), len(ended)
        ),
        "excused": sum(r["attendance_status"] == "excused" for r in ended),
        "unrecorded": sum(r["attendance_status"] == "unrecorded" for r in ended),
    }


def report(settings, filters, clock):
    start, end = date_bounds(filters.start, filters.end, filters.timezone)
    as_of = stamp(clock.now())
    with connect(settings) as conn:
        selected_sessions = [
            dict(r)
            for r in conn.execute(
                "SELECT s.*,c.title FROM sessions s JOIN courses c ON c.id=s.course_id WHERE starts_at_utc>=? AND starts_at_utc<? AND (? IS NULL OR course_id=?) ORDER BY starts_at_utc",
                (start, end, filters.course_id, filters.course_id),
            )
        ]
        rows = [
            dict(r)
            for r in conn.execute(
                "SELECT e.*,l.display_name,d.name department,s.starts_at_utc,s.ends_at_utc,s.completion_due_at_utc,s.status session_status,c.title course,s.course_id FROM enrollments e JOIN learners l ON l.id=e.learner_id JOIN departments d ON d.id=e.department_id_at_registration JOIN sessions s ON s.id=e.session_id JOIN courses c ON c.id=s.course_id WHERE s.starts_at_utc>=? AND s.starts_at_utc<? AND (? IS NULL OR s.course_id=?) AND (? IS NULL OR e.department_id_at_registration=?) ORDER BY e.id",
                (
                    start,
                    end,
                    filters.course_id,
                    filters.course_id,
                    filters.department_id,
                    filters.department_id,
                ),
            )
        ]
    for r in rows:
        r["month"] = (
            utc(r["starts_at_utc"]).astimezone(ZoneInfo(filters.timezone)).strftime("%Y-%m")
        )
        r["overdue"] = (
            r["status"] == "registered"
            and r["session_status"] in {"scheduled", "completed"}
            and r["completion_due_at_utc"] < as_of
            and r["completion_status"] != "completed"
        )
        r["late_completion"] = bool(
            r["completed_at"] and r["completed_at"] > r["completion_due_at_utc"]
        )
        r["as_of_utc"], r["display_timezone"], r["data_source"] = (
            as_of,
            filters.timezone,
            "Synthetic data / Portfolio demo",
        )
    summary = metrics(rows, as_of)
    eligible = [s for s in selected_sessions if s["status"] in {"scheduled", "completed"}]
    summary["capacity"] = (
        None
        if filters.department_id is not None
        else fraction(summary["registrations"], sum(s["capacity"] for s in eligible))
    )
    per_session = []
    if filters.department_id is None:
        for s in eligible:
            count = sum(r["session_id"] == s["id"] and r["status"] == "registered" for r in rows)
            per_session.append(
                {"session_id": s["id"], "course": s["title"], **fraction(count, s["capacity"])}
            )
    groups = {}
    for field in ("department", "course", "month"):
        groups[field] = [
            {field: name, **metrics([r for r in rows if r[field] == name], as_of)}
            for name in sorted({r[field] for r in rows})
        ]
    return {
        "summary": summary,
        "rows": rows,
        "groups": groups,
        "sessions": per_session,
        "as_of": as_of,
        "timezone": filters.timezone,
    }


CSV_COLUMNS = (
    "id",
    "learner_id",
    "display_name",
    "department",
    "session_id",
    "course",
    "starts_at_utc",
    "ends_at_utc",
    "session_status",
    "status",
    "registration_cycle",
    "attendance_status",
    "completion_status",
    "completed_at",
    "completion_due_at_utc",
    "overdue",
    "late_completion",
    "as_of_utc",
    "display_timezone",
    "data_source",
)


def safe_cell(value):
    if isinstance(value, str) and (
        value.lstrip().startswith(("=", "+", "-", "@")) or value.startswith(("\t", "\r", "\n"))
    ):
        return "'" + value
    return value


def export_csv(rows):
    out = io.StringIO(newline="")
    writer = csv.DictWriter(out, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    writer.writerows({key: safe_cell(row.get(key, "")) for key in CSV_COLUMNS} for row in rows)
    return out.getvalue().encode("utf-8-sig")
