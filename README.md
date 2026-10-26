# LearnOps Flow

**Learning Operations Automation Platform**

LearnOps Flow is a planned portfolio project for managing training schedules, enrollment, attendance, completion records, rule-based communications, and operational reporting.

**Status: Specification stage.** This README describes the intended product. Application development, testing, and deployment have not been verified. All demonstration data will be synthetic, and notification delivery will be simulated.

## Why this project

Training operations often involve coordinating schedules, maintaining registration lists, tracking attendance, preparing reminders, and assembling reports. LearnOps Flow explores how these activities can be connected through one consistent workflow with explicit business rules and traceable records.

The project is intended to demonstrate skills relevant to Learning Operations, Training Coordination, L&D Coordination, and Learning Systems roles.

## Planned V1 workflow

1. Create a course and publish a training session.
2. Register synthetic learners while enforcing capacity and duplicate-registration rules.
3. Generate confirmation and reminder messages using predefined rules.
4. Record attendance and completion after the session.
5. Identify overdue incomplete records and generate follow-up messages.
6. Review department and course reporting, inspect the underlying records, and export CSV files.

## Planned features

| Module | Intended scope |
|---|---|
| Training calendar and enrollment | Course catalog, dated session views, registration, cancellation, and capacity controls |
| Attendance and completion | Separate attendance and completion states, batch updates, completion rules, and audit records |
| Communication automation | Message templates, rule evaluation, duplicate prevention, retries, and simulated delivery |
| Reporting | Documented metric definitions, filters, charts, record-level details, and CSV exports |

These are planned capabilities, not a list of completed features.

## Proposed technology stack

- **Python** for application and business logic.
- **Streamlit** for forms, operational views, and dashboards.
- **SQLite** for local persistence and transactional updates.
- **pandas** for reporting and data preparation.
- **pytest** for business-rule testing, with selected UI smoke checks.
- **Ruff and GitHub Actions** for development checks.

The architecture will separate the interface, business services, reporting queries, and database access. Compatible dependency versions will be selected and recorded during implementation.

## Specification and development

The complete development specification is maintained in [`PROJECT_SPEC.md`](PROJECT_SPEC.md). It covers requirements, state transitions, the data model, acceptance criteria, a proposed 14-day plan, deployment expectations, and implementation instructions.

The specification is written in Chinese. This README and the planned application interface use English.

There are no verified installation or launch instructions yet. Add those instructions after the application exists and has been reproduced in a clean environment. Do not treat the target commands in the specification as working software at this stage.

## Data and demonstration boundaries

- Use synthetic learners, departments, courses, and training records only.
- Use fictitious email addresses such as `learner001@example.com`.
- Simulate notification delivery; do not send real emails or text messages.
- Demonstration role selection will not represent real authentication or authorization.
- The planned public demonstration will be read-only; the local demonstration will support controlled edits.
- Label charts, screenshots, exports, and demonstrations as synthetic-data examples.

V1 will not include a full LMS, content hosting, SCORM/xAPI, production identity management, or real HRIS integrations.

## Validation plan

Acceptance criteria in the specification include:

- Capacity enforcement, including competing registrations for the final seat.
- Registration cancellation and re-registration without duplicate records.
- Consistent attendance and completion rules.
- Idempotent message generation, retry limits, and stale-message cancellation.
- Reporting with known numerators and denominators, including empty datasets.
- Time-zone boundaries, safe CSV exports, and service-level read-only enforcement.
- Reproducible setup and a complete demonstration workflow.

Actual test commands, results, environment details, screenshots, and limitations will be documented after implementation. No test results or business outcomes are claimed here.

## Roadmap

- **V1:** Complete the training operations workflow with synthetic data and simulated communications.
- **V2:** Evaluate an API layer, PostgreSQL, and authenticated integrations when requirements justify them.
- **Later AI exploration:** Human-reviewed communication drafts and summaries grounded in aggregate reporting, with explicit evaluation criteria.

## Portfolio presentation

Present LearnOps Flow as a personal portfolio project. Describe implemented capabilities only after they have been built and verified. Any measured improvements must identify the synthetic test conditions and must not be presented as results from a real organization.

AI-assisted development methods and the author's contributions should be documented accurately as implementation progresses.

## License

A license has not yet been selected. The repository owner should choose one before presenting the project as open-source software.
