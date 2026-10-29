from learning_ops.db import connect


def catalog(settings, table):
    if table not in {
        "courses",
        "learners",
        "departments",
        "message_templates",
        "communication_jobs",
        "audit_events",
        "demo_metadata",
    }:
        raise ValueError("Unsupported catalog")
    with connect(settings) as conn:
        return [dict(row) for row in conn.execute(f"SELECT * FROM {table}")]


def sessions(settings):
    with connect(settings) as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT s.*,c.title,COALESCE(e.registered,0) registered FROM sessions s JOIN courses c ON c.id=s.course_id LEFT JOIN (SELECT session_id,count(*) registered FROM enrollments WHERE status='registered' GROUP BY session_id) e ON e.session_id=s.id ORDER BY s.starts_at_utc"
            )
        ]


def roster(settings, session_id=None, learner_id=None):
    with connect(settings) as conn:
        return [
            dict(row)
            for row in conn.execute(
                "SELECT e.*,l.display_name,d.name department,c.title,s.starts_at_utc,s.ends_at_utc,s.completion_due_at_utc,s.status session_status FROM enrollments e JOIN learners l ON e.learner_id=l.id JOIN departments d ON d.id=e.department_id_at_registration JOIN sessions s ON s.id=e.session_id JOIN courses c ON c.id=s.course_id WHERE (? IS NULL OR e.session_id=?) AND (? IS NULL OR e.learner_id=?) ORDER BY e.id",
                (session_id, session_id, learner_id, learner_id),
            )
        ]
