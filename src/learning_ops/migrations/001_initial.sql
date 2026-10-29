CREATE TABLE departments (id INTEGER PRIMARY KEY, name TEXT NOT NULL UNIQUE);
CREATE TABLE learners (
 id INTEGER PRIMARY KEY, synthetic_employee_code TEXT NOT NULL UNIQUE,
 display_name TEXT NOT NULL, email TEXT NOT NULL UNIQUE CHECK(email LIKE '%@example.com'),
 department_id INTEGER NOT NULL REFERENCES departments(id), active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), created_at TEXT NOT NULL
);
CREATE TABLE courses (
 id INTEGER PRIMARY KEY, title TEXT NOT NULL, category TEXT NOT NULL, description TEXT NOT NULL,
 completion_rule TEXT NOT NULL CHECK(completion_rule IN ('attendance_only','attendance_plus_confirmation')),
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), created_at TEXT NOT NULL
);
CREATE TABLE sessions (
 id INTEGER PRIMARY KEY, course_id INTEGER NOT NULL REFERENCES courses(id), facilitator_name TEXT NOT NULL,
 delivery_mode TEXT NOT NULL CHECK(delivery_mode IN ('online','in_person')), location TEXT NOT NULL,
 starts_at_utc TEXT NOT NULL, ends_at_utc TEXT NOT NULL CHECK(ends_at_utc > starts_at_utc),
 timezone TEXT NOT NULL, capacity INTEGER NOT NULL CHECK(typeof(capacity)='integer' AND capacity>0),
 completion_due_at_utc TEXT NOT NULL CHECK(completion_due_at_utc >= ends_at_utc),
 completion_rule_snapshot TEXT CHECK(completion_rule_snapshot IN ('attendance_only','attendance_plus_confirmation')),
 status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','scheduled','completed','cancelled')),
 created_at TEXT NOT NULL, updated_at TEXT NOT NULL
);
CREATE TABLE enrollments (
 id INTEGER PRIMARY KEY, learner_id INTEGER NOT NULL REFERENCES learners(id), session_id INTEGER NOT NULL REFERENCES sessions(id),
 department_id_at_registration INTEGER NOT NULL REFERENCES departments(id),
 status TEXT NOT NULL CHECK(status IN ('registered','cancelled')),
 registration_cycle INTEGER NOT NULL DEFAULT 1 CHECK(registration_cycle>0), registered_at TEXT NOT NULL,
 cancelled_at TEXT, cancellation_reason TEXT,
 attendance_status TEXT NOT NULL DEFAULT 'unrecorded' CHECK(attendance_status IN ('unrecorded','present','absent','excused')),
 completion_status TEXT NOT NULL DEFAULT 'not_completed' CHECK(completion_status IN ('not_completed','completed')),
 completed_at TEXT, completion_revision INTEGER NOT NULL DEFAULT 0 CHECK(completion_revision>=0), updated_at TEXT NOT NULL,
 UNIQUE(learner_id,session_id),
 CHECK((completion_status='not_completed' AND completed_at IS NULL) OR (completion_status='completed' AND completed_at IS NOT NULL AND attendance_status='present'))
);
CREATE TABLE message_templates (
 id INTEGER PRIMARY KEY, message_type TEXT NOT NULL CHECK(message_type IN ('confirmation','reminder','cancellation','completion','followup')),
 version INTEGER NOT NULL CHECK(version>0), subject_template TEXT NOT NULL, body_template TEXT NOT NULL,
 active INTEGER NOT NULL DEFAULT 1 CHECK(active IN (0,1)), UNIQUE(message_type,version)
);
CREATE UNIQUE INDEX one_active_template ON message_templates(message_type) WHERE active=1;
CREATE TABLE communication_jobs (
 id INTEGER PRIMARY KEY, enrollment_id INTEGER NOT NULL REFERENCES enrollments(id), registration_cycle INTEGER NOT NULL,
 completion_revision INTEGER NOT NULL DEFAULT 0,
 message_type TEXT NOT NULL CHECK(message_type IN ('confirmation','reminder','cancellation','completion','followup')),
 template_id INTEGER NOT NULL REFERENCES message_templates(id), idempotency_key TEXT NOT NULL UNIQUE,
 recipient_snapshot TEXT NOT NULL, subject_rendered TEXT NOT NULL, body_rendered TEXT NOT NULL, due_at_utc TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','simulated_sent','failed','cancelled')),
 attempt_count INTEGER NOT NULL DEFAULT 0 CHECK(attempt_count BETWEEN 0 AND 3), last_error TEXT,
 created_at TEXT NOT NULL, processed_at TEXT, cancellation_reason TEXT
);
CREATE TABLE audit_events (
 id INTEGER PRIMARY KEY, actor_demo_role TEXT NOT NULL, entity_type TEXT NOT NULL, entity_id INTEGER NOT NULL,
 action TEXT NOT NULL, before_json TEXT, after_json TEXT, reason TEXT,
 occurred_at_utc TEXT NOT NULL, business_as_of_utc TEXT NOT NULL
);
CREATE TABLE demo_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE INDEX sessions_start ON sessions(starts_at_utc);
CREATE INDEX enrollment_session_status ON enrollments(session_id,status);
CREATE INDEX jobs_status_due ON communication_jobs(status,due_at_utc);
