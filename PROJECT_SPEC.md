# LearnOps Flow — Learning Operations Automation Platform

**Project specification and development handoff, V1.1, 2026-10-25.** This English version condenses the original Chinese planning document while retaining its requirements. The original is preserved in Git history at commit `f383f68fe2384ef1824d8903612cd9041fb4e9e2`. This specification describes targets, not evidence of implementation, validation, deployment, or business results. For actual status see [README](README.md) and [validation](docs/validation.md).

## 1. Purpose and assumptions

Build a reproducible, explainable portfolio prototype for a fictional learning and development team, connecting scheduling, registration, attendance, completion, rule-driven communications and operational reporting. It is not a complete LMS or a production enterprise system. The scenario assumes one fictional organization, one operations team, small internal training, and single-session courses. No personal experience, real user research, hiring outcome, or organizational benefit is implied.

Potential portfolio roles include Learning Operations Coordinator/Specialist, Training Coordinator/Administrator, L&D Coordinator, Learning Program/Program Operations Coordinator, LMS Administrator/Learning Systems Coordinator, and Learning Operations/L&D Reporting Analyst. Choose roles consistent with actual experience; the project alone does not establish senior engineering, AI engineering, management, or commercial LMS administration experience.

Success means an interviewer can understand the business problem in 60 seconds and see the workflow in 3–5 minutes; a clean environment can run it; data is reproducible; critical rules are tested; and the author can explain the data model, denominators, exceptions, privacy boundaries and architecture. Any efficiency comparison requires a documented controlled synthetic task, baseline, samples, environment and measurement scope; do not imply real-world results.

## 2. Scope, users and priorities

P0 covers four end-to-end modules: (1) a course catalog and date-grouped training calendar with filters, drafts, publication, enrollment, cancellation and capacity; (2) session rosters, individual and atomic batch attendance, completion rules, correction reasons and audit; (3) confirmation, reminder, cancellation, completion and overdue follow-up templates, previews, queues, deduplication, retries and mock delivery; (4) filtered enrollment, attendance, completion, overdue and capacity reporting, charts, traceable detail and CSV. Include constraints, reproducible seed, tests, README and a local demonstration. A list or table is sufficient for the calendar.

P1, only after P0, includes calendar polish, additional charts, a public read-only demo and a short video. Local demonstration is an acceptable delivery when public deployment is unbuilt and clearly labelled.

Demo roles: Coordinator manages sessions, registrations, records, communications and exports; Learner selects a fictional identity, views available sessions, registers, cancels and views their records; L&D Manager views, filters and exports summaries. Label the selector **Demo role — no authentication**. Public read-only mode must disable all writes, imports, queue execution, clock changes and reset; local identities are fictional.

V1 excludes content/video hosting, authoring, SCORM/xAPI, exams, certificates, a complete LMS, real HRIS/LMS/email/SSO/payment/Teams/calendar integrations, real authentication or production permissions, multi-tenancy, enterprise SLAs, real messages or employee data, waitlists, recurring schedules, multi-session hours, budgets, vendor management, automated recommendations, AI grading or employee evaluation. Do not claim learning, performance or compliance improvements. Avoid unnecessary microservices, brokers and complex frontend infrastructure.

The standard demo creates and publishes a future ten-seat session, registers fictional learners, demonstrates duplicate/full rejection, previews confirmation, advances a labelled Demo Clock, generates and simulates reminders, records attendance and an attended-but-incomplete learner, advances past the due date, previews follow-up, and shows report numerators/denominators, CSV, deduplication and audit.

## 3. Functional rules

### FR-01 Courses and sessions

Courses have title, category, description, completion rule and active flag. Sessions have course, facilitator display name, online/in-person mode, fictional location/link, start/end, IANA timezone, positive integer capacity, completion deadline, status, and timestamps. Transitions: `draft → scheduled → completed`, or `draft/scheduled → cancelled`. Completed means operationally closed, not that all learners completed; closure requires the end time to have arrived. End must follow start; deadline must be at or after end; publication requires start strictly after the business clock.

Drafts are editable. After publication lock course, time, location, mode, completion rule and deadline. Reschedule by cancelling and creating a new session without automatic registration migration. Capacity may change but not below active registrations; audit the change. Only drafts with no enrollment history may be deleted; otherwise retain history through cancellation/deactivation.

### FR-02 Enrollment

One record per learner/session, with `registered`/`cancelled` state. `registration_cycle` starts at 1 and increments upon re-registration. Registration requires an active learner and course, a scheduled session, time before start and available capacity. Check capacity and write enrollment in the same write transaction; two concurrent requests must not claim the last seat. Read rosters and counts from the database, not stale UI state.

Before start, cancellation frees a seat and invalidates obsolete reminders. After start, ordinary retrospective cancellation is prohibited; erroneous entries require an explicitly recorded audited correction. Session cancellation sets all active enrollments to cancelled with `session_cancelled` reason, cancels unprocessed related jobs and queues cancellation notices. Re-registration rechecks all eligibility and capacity rules.

### FR-03 Attendance and completion

Attendance is `unrecorded`, `present`, `absent` or `excused`; completion is `not_completed` or `completed`. Derive overdue from deadline and clock rather than storing a separate boolean. Record only active enrollments of non-cancelled sessions after the session ends. Snapshot the course rule on publication: `attendance_only` maps present to completed and all other attendance states to not_completed; `attendance_plus_confirmation` requires present plus coordinator confirmation, and other attendance states cannot be completed.

Completion timestamps must be between session end and the current business clock; late entries are allowed and displayed. Corrections require a reason and before/after audit. Revocation cancels undelivered completion messages but retains simulated-sent history. Each transition from incomplete to complete increments `completion_revision`. Validate and save a batch atomically, identifying the erroneous row on failure.

### FR-04 Communications

Automation means rule generation and on-demand batch simulation, not real email or a continuously running scheduler. Generate confirmation immediately on registration/re-registration; reminder when an active registration enters the 24-hour pre-start window, including late registrations but never after start; cancellation immediately on learner/session cancellation, distinguishing reason; completion when transitioning to completed; follow-up when deadline is strictly past and an active registration remains incomplete. Deduplicate by enrollment ID + cycle + type, adding completion revision for completion. A follow-up occurs at most once per cycle.

Templates include subject, body, fictional learner, course, session date and timezone; unknown variables must block generation without unresolved placeholders. Store rendered content and recipient snapshots. States are `pending`, `simulated_sent`, `failed`, `cancelled`; label processing **Simulated delivery**. Enforce unique `idempotency_key` in SQLite. Enrollment/cancellation/completion and associated jobs must commit together; repeat scans and UI reruns must not duplicate jobs.

Provide preview, Run rules, Process pending, Retry failed and message log. Total attempts are capped at three, after which manual handling is indicated. Revalidate state immediately before processing: cancel stale reminders, expired reminders and follow-ups for completed learners, recording reasons. Use a deterministic injectable-failure mock with no SMTP, real credentials or external delivery. Provide a repeatable one-shot command for a future external scheduler; do not start an infinite loop from Streamlit. Demo Clock affects business time; audit records actual system time separately; public mode cannot change the clock.

### FR-05 Reporting and export

Unit is an enrollment record; separately show distinct learners. Filter by session start date in the selected business timezone, translating inclusive start/end dates to a UTC half-open interval. Course and registration-department filters apply to the same details used by tables, charts and exports.

`R` = active registrations in non-cancelled sessions; `E` = R where end ≤ as-of, including scheduled sessions not yet manually closed; `P` = E marked present; `C` = E marked completed; `D` = E with due date strictly before as-of and still incomplete. Show active registrations and distinct learners, with cancellations separately. Attendance = P/E; completion = C/E; overdue = D / overdue-due subset of E; coverage = recorded attendance / E. Excused and unrecorded remain in E and are shown separately; unrecorded is not automatically absent. Utilization = active registrations / session capacity, aggregated as total registrations / total capacity, not an average of percentages. When a department filter is active hide utilization and explain that capacity is shared, not a departmental quota. All zero denominators show N/A.

Provide department, course and month breakdowns and at least department completion and monthly active-registration charts. Show numerators, denominators, filters, as-of, timezone and synthetic-data label; explain charts in text and do not rely on color alone. UTF-8 CSV may use a BOM, has stable headers, and protects text beginning with dangerous spreadsheet formula prefixes such as `=`, `+`, `-`, `@`. Reports describe current persisted state by session date, not historical snapshots; changing Demo Clock must not masquerade as reconstructing the past.

## 4. Nonfunctional requirements and architecture

Use Python, Streamlit and SQLite, with pandas for reporting, standard datetime/zoneinfo and tzdata if needed, pytest, Ruff and CI. Python 3.12 is the initial compatibility baseline, subject to actual validation. Pin dependencies; document actual versions. Separate UI, services, queries and persistence. Business services must be testable without Streamlit; session state is not the source of business truth. Parameterize SQL. Use SQLite for the assumed small single-instance workload; revisit it for shared persistence, more writers or multi-instance needs. Do not claim capacity guarantees.

Reproducibility requires migrations, fixed seeds, reset instructions and clean-environment verification. Enable foreign keys on every connection; use unique keys and CHECK constraints for enums, positive capacity and nonnegative attempts; validate time ordering and cross-table rules in services. Use short `BEGIN IMMEDIATE` registration transactions and finite lock waits with understandable retry errors. Do not share unmanaged connections across requests or expose database files in a static download directory. Reset only by an explicit local command targeting the configured demo database; never overwrite data on application startup.

Store fixed-format UTC timestamps, e.g. `2026-10-25T14:00:00Z`; use explicit IANA timezones for input/output. Reject nonexistent DST times and require an explicit choice for ambiguous times. Public read-only must be enforced in services, not just by hidden UI controls; log no secrets. Aim for major warm queries under two seconds on 200 learners, 24 sessions and roughly 400 registrations, measuring each ten times and reporting median, maximum, machine and scope; no cloud SLA claim. Use labelled controls, keyboard access, sufficient contrast and textual states; manually inspect main paths without claiming accessibility certification.

## 5. Data model and seed

Relationships: departments → learners; courses → sessions; learners and sessions → enrollments; enrollments and templates → communication jobs. Audit events track changes; schema migrations track versions. Attendance/completion are on enrollments for single-session V1.

- `departments`: id, unique name. `learners`: id, unique synthetic code, display name, unique fictional email, department FK, active, created_at.
- `courses`: id, title, category, description, completion_rule, active, created_at. `sessions`: id, course FK, facilitator, delivery mode, location, UTC start/end, timezone, capacity, UTC completion deadline, completion-rule snapshot, status, created/updated timestamps.
- `enrollments`: id, learner/session FKs and unique pair, department-at-registration FK, status, registration cycle, registered/cancelled times and reason, attendance, completion, completed_at, completion revision, updated_at. Snapshot department at initial registration; refresh on re-registration and retain audit history.
- `message_templates`: id, type, version, subject, body, active; unique type/version. `communication_jobs`: id, enrollment FK, cycle, type, template FK, unique idempotency key, recipient/subject/body snapshots, UTC due time, state, attempts, last error, created/processed times and cancellation reason.
- `audit_events`: id, demo actor, entity type/id, action, before/after JSON, reason, actual UTC operation time and business as-of. Audit registration, attendance, completion and message-state updates in the same transaction. `schema_migrations`: version and applied UTC time. Index session start, enrollment session/status and job status/due.

Seed target: 200 fictional learners, six departments, eight courses, 24 sessions and approximately 400 registrations, respecting capacity and states. Use fixed seed (e.g. 42) and explicit base date; same inputs produce the same logical data. Cover past/future/cancelled/full sessions, both completion rules, absent, excused, unrecorded, late completion, failure and retry. Use addresses such as `learner001@example.com`, never real names, employee IDs, contact details, HR data or other sensitive information. Label app, README, exports and screenshots **Synthetic data / Portfolio demo**. No arbitrary CSV upload. Never commit secrets, logs or demo database; commit the generator and small deterministic fixtures. Public data must be rebuildable without persistence promises. Do not claim GDPR, PIPEDA, SOC 2 or other compliance.

## 6. Acceptance criteria

Record actual environment, revision, commands, results, failures, performance and limitations in `docs/validation.md`; these criteria are requirements, not test results.

| ID | Required scenario and result |
|---|---|
| AC-01 | Normal and repeated registration: one active record and one confirmation per cycle. |
| AC-02 | Two independent connections compete for one seat: at most one succeeds; understandable failure. |
| AC-03 | Cancel/re-register: seat released, old reminder cancelled, cycle incremented, new confirmation. |
| AC-04 | Draft, cancelled or started session registration rejected without database changes. |
| AC-05 | Session cancellation cancels active registrations and stale reminders, with one cancellation per cycle. |
| AC-06 | Both completion rules, invalid absence completion and due-time boundaries behave correctly. |
| AC-07 | One invalid batch row rolls back the entire batch. |
| AC-08 | Repeated rule scans and processing do not duplicate or redeliver jobs. |
| AC-09 | Mock failure is visible; successful jobs are not retried; maximum three attempts. |
| AC-10 | A reminder made stale by cancellation or session start is cancelled before delivery. |
| AC-11 | Revocation and reconfirmation retain audit, cancel pending old notice and create a new revision. |
| AC-12 | Fixed report fixture handles future, cancelled, excused, unrecorded and empty sets, with N/A for zero denominator. |
| AC-13 | Local date boundaries are inclusive/exclusive as specified; ambiguous and nonexistent DST times are handled. |
| AC-14 | CSV and UI use identical filtered rows; formula prefixes are protected. |
| AC-15 | Local records survive restart; UI reruns do not create duplicates. |
| AC-16 | Public UI exposes no write controls and direct write-service calls fail without changing data. |
| AC-17 | Successful changes have before/after audit; failed transactions leave no orphan jobs or audit. |
| AC-18 | Clean install, initialization, seed, tests and launch follow documented commands. |

Independent fixed fixture: two ended, overdue sessions with capacity five each and eight active enrollments: six present, one absent, one unrecorded, with five completed among the six present. Expected attendance 6/8 = 75%, completion 5/8 = 62.5%, overdue 3/8 = 37.5%, coverage 7/8 = 87.5%, utilization 8/10 = 80%. Add a cancelled enrollment, a cancelled session and a future session with two registrations/capacity four: ended rates remain unchanged, total active registrations become ten and utilization 10/14. Change one present learner to excused, revoking completion if necessary: denominator remains eight and numerators change accordingly.

All P0 criteria must pass before marking V1 complete. Test key business services and at least UI startup/main paths; CI installs dependencies, runs lint and tests without real services. No fake badges, invented status, real data or hardcoded secrets. Screenshots must come from the running application. Coverage percentage is not a substitute for rule correctness; report unrun or failed checks.

## 7. Setup, deployment and documentation

Expected interfaces, subject to actual implementation and verification:

```bash
python -m venv .venv
python -m pip install -r requirements-dev.txt
python -m pip install -e . --no-deps
python -m scripts.init_db
python -m scripts.seed_demo --seed 42 --base-date 2026-10-25
python -m pytest
python -m ruff check .
python -m streamlit run app.py
python -m scripts.run_communications --as-of 2026-10-25T14:00:00Z --mode mock
```

Default DB `data/demo.sqlite3`; configuration includes `APP_MODE=local_demo|public_readonly`, `DATABASE_PATH`, `DISPLAY_TIMEZONE=America/Toronto`, `MESSAGE_PROVIDER=mock`. Default application mode must be public read-only; local writing requires explicit opt-in. `.env.example` must contain no secrets. Existing data must cause seed to refuse rather than silently clear; provide explicit reset instructions.

Local demo is single-user, synthetic and mock-only, with persistent data across restarts and a labelled Demo Clock. Troubleshoot dependencies, missing database, locks, occupied port and empty date filters. Public demo, if built, initializes synthetic data before access, provides a fixed explicit as-of, disables all writes/imports/reset/queue execution and does not promise cloud SQLite persistence or run a permanent scheduler. No fabricated demo link; mark deployment planned until real. Verify current platform compatibility before any deployment.

English README should distinguish implemented features from roadmap and include the problem, users, workflow, actual screenshots/demo when available, architecture and entity relationships, setup/configuration/seed/reset, roles, clock, mock and public boundaries, metrics and hand-checkable example, test evidence, privacy/deployment limitations, V2, truthful author/AI contributions and license status. The owner must choose a license; do not claim open-source licensing before that. Suggested 3–5 minute narrative: problem, scheduling/enrollment, attendance/completion/mock exceptions, reports, and architecture/tests/limits.

## 8. Delivery plan, provenance and V2

The original 14-day plan was a suggested 2–3 hour/day timebox, not a waiting period or delivery guarantee: clarify process and scope; scaffold dependencies; migrate/seed; schedule; enrollment/capacity; attendance/completion; verify core workflow; templates/queue; mock/retries; reporting fixture; charts/CSV; acceptance/performance; README/deployment preparation; clean reproduction and portfolio review. Do not add charts before the core workflow is stable or mark V1 complete before critical acceptance passes.

Implement in order: configuration/injectable clock/migrations/seed; sessions, enrollment, capacity, cancellation and audit; attendance/completion and atomic corrections; templates/queue/rules/mock/deduplication/retry; shared reporting/fixed fixture/charts/safe CSV; public boundaries, errors, README and validation. Preserve existing repository work, check the environment, test each stage, reproduce in a clean environment, investigate failures, and document actual evidence. Do not weaken acceptance criteria or add unrelated MVP scope. This specification does not authorize real data, actual messages, paid services or external publication.

Only describe implemented and validated work as built/tested. Use “in progress” when incomplete, “simulated notifications” for mock delivery, synthetic counts for seed data, and “deployed” only after actual deployment. Do not invent numerical gains or commercial results. The author should be able to explain separate enrollment/attendance/completion, future-session denominators, registration cycles, last-seat concurrency, role vs authentication, deduplication and AI-assisted development.

Revisit decisions when justified: API/FastAPI for a second frontend or integration, with versioned contracts, authentication and authorization tests; PostgreSQL for shared/multi-writer persistence, with migration, concurrency and backup/restore evidence; real communications only with an authorized use case, scheduler/worker, transactional outbox, delivery receipts, retry/backoff and credential/data controls; AI drafts or aggregate summaries only after core stability, human review, fixed evaluation and cost/latency/factuality evidence. AI must not alter attendance/completion, rank employees, make hiring decisions, send real personal learning records externally, invent causes or benefits, or bypass review. Record core-rule changes and affected acceptance cases in `docs/decisions.md`.

## 9. Definition of done and synchronization history

Completion requires a demonstrable four-module P0 workflow; passing capacity/duplicate/cancellation/completion/deduplication/retry checks; fixed metrics and consistent charts/CSV; synthetic-only data, clear mock labelling and public read-only enforcement; clean setup/seed/tests/launch; consistent README/architecture/metrics/decisions/demo/validation; evidence-based portfolio claims; and explicit limitations and V2. Do not claim completion before all corresponding evidence exists.

After each delivery of local updates, offer reviewable files and ask whether to synchronize GitHub. Do not commit or push a batch without its specific authorization; explain actual target, files and result, and never claim an unsuccessful sync. The user has authorized the present implementation and English-specification batch. The original 2026-10-25 V1.1 update established the LearnOps Flow name and updated the title, examples, portfolio title and implementation instructions without changing scope. The original Chinese V1.1 remains recoverable in the prior Git commit referenced above.
