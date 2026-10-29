from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pandas as pd
import streamlit as st

from learning_ops.clock import FixedClock, local_to_utc, stamp, utc
from learning_ops.config import DomainError, Settings
from learning_ops.reporting import Filters, export_csv, report, safe_cell
from learning_ops.repository import catalog, roster, sessions
from learning_ops.services.communications import (
    TYPES,
    VARIABLES,
    Communications,
    MockProvider,
    render,
)
from learning_ops.services.completion import Completion
from learning_ops.services.enrollment import Enrollment
from learning_ops.services.scheduling import SESSION_FIELDS, Scheduling

AREAS = [
    "Overview",
    "Training calendar",
    "Enrollments",
    "Attendance & completion",
    "Communications",
    "Reports",
    "Audit trail",
]


def table(rows):
    if rows:
        # Streamlit also exposes its own CSV download on dataframes.
        st.dataframe(pd.DataFrame(rows).map(safe_cell), hide_index=True, width="stretch")
    else:
        st.info("No records in this view. Adjust the filters or create a synthetic demo record.")


def choose(label, records, text, key, allow_all=False):
    lookup = {r["id"]: r for r in records}
    options = ([None] if allow_all else []) + list(lookup)
    return st.selectbox(
        label, options, format_func=lambda i: "All" if i is None else text(lookup[i]), key=key
    )


def done(message):
    st.session_state["notice"] = message
    st.rerun()


def ratio(value):
    return "N/A" if value["rate"] is None else f"{value['rate']:.1%}"


def summary_cards(data):
    summary = data["summary"]
    columns = st.columns(4)
    columns[0].metric("Active registrations", summary["registrations"])
    columns[0].caption(
        f"{summary['distinct_learners']} distinct learners · {summary['cancelled']} cancelled"
    )
    for column, key, label in zip(
        columns[1:],
        ("attendance", "completion", "overdue"),
        ("Attendance rate", "Completion rate", "Overdue incomplete rate"),
    ):
        value = summary[key]
        column.metric(label, ratio(value))
        column.caption(f"{value['numerator']} / {value['denominator']} registrations")


def report_filters(settings, clock, prefix):
    all_sessions = sessions(settings)
    dates = [
        utc(s["starts_at_utc"]).astimezone(ZoneInfo(settings.display_timezone)).date()
        for s in all_sessions
    ]
    today = clock.now().astimezone(ZoneInfo(settings.display_timezone)).date()
    cols = st.columns(4)
    with cols[0]:
        start = st.date_input("Start date", min(dates, default=today), key=prefix + "start")
    with cols[1]:
        end = st.date_input("End date", max(dates, default=today), key=prefix + "end")
    with cols[2]:
        course_id = choose(
            "Course", catalog(settings, "courses"), lambda r: r["title"], prefix + "course", True
        )
    with cols[3]:
        department_id = choose(
            "Department",
            catalog(settings, "departments"),
            lambda r: r["name"],
            prefix + "dept",
            True,
        )
    return Filters(start, end, settings.display_timezone, course_id, department_id)


def overview(settings, clock):
    st.subheader("A clear view of learning operations")
    st.write("Coordinate training, keep records consistent, and see what needs attention.")
    data = report(settings, report_filters(settings, clock, "overview_"), clock)
    summary_cards(data)
    st.divider()
    left, right = st.columns([3, 2])
    with left:
        st.markdown("### Coming up")
        upcoming = [
            s
            for s in sessions(settings)
            if s["status"] == "scheduled" and s["starts_at_utc"] > stamp(clock.now())
        ][:5]
        for s in upcoming:
            with st.container(border=True):
                st.markdown(f"**{s['title']}**")
                local = utc(s["starts_at_utc"]).astimezone(ZoneInfo(settings.display_timezone))
                st.write(f"{local:%a, %b %d · %H:%M} {settings.display_timezone}")
                st.caption(
                    f"Session #{s['id']} · {s['registered']} of {s['capacity']} seats · {s['delivery_mode']}"
                )
        if not upcoming:
            st.info("No upcoming scheduled sessions in the current database.")
    with right:
        st.markdown("### Operations checklist")
        with st.container(border=True):
            st.write("1. Publish a future training session.")
            st.write("2. Register synthetic learners.")
            st.write("3. Preview and simulate communications.")
            st.write("4. Record attendance after the session.")
            st.write("5. Review completion and export a report.")
        jobs = catalog(settings, "communication_jobs")
        st.metric(
            "Messages awaiting review", sum(j["status"] in {"pending", "failed"} for j in jobs)
        )
        st.caption("Simulated delivery only. Rule scans and processing run on demand.")
        st.caption(
            f"Record coverage: {ratio(data['summary']['coverage'])}. Unrecorded attendance is not an explicit absence."
        )


def course_form(settings, clock):
    with st.expander("Course catalog · create or edit"):
        courses = catalog(settings, "courses")
        selected = st.selectbox(
            "Edit course",
            [None] + [c["id"] for c in courses],
            format_func=lambda i: "Create new course"
            if i is None
            else next(c["title"] for c in courses if c["id"] == i),
        )
        old = next((c for c in courses if c["id"] == selected), {})
        with st.form(f"course_{selected}"):
            title = st.text_input("Course title", old.get("title", ""))
            category = st.text_input("Category", old.get("category", "Core skills"))
            description = st.text_area(
                "Description", old.get("description", "Synthetic training demo.")
            )
            rules = ["attendance_only", "attendance_plus_confirmation"]
            rule = st.selectbox(
                "Completion rule", rules, index=rules.index(old.get("completion_rule", rules[0]))
            )
            active = st.checkbox("Course is active", bool(old.get("active", True)))
            if st.form_submit_button("Save course"):
                Scheduling(settings, clock).save_course(
                    title, category, description, rule, active, selected
                )
                done("Course saved. Published session rules keep their original snapshot.")


def draft_form(settings, clock):
    courses = catalog(settings, "courses")
    if not courses:
        st.info("Create a course first.")
        return
    with st.expander("Create or edit a draft session"):
        drafts = [s for s in sessions(settings) if s["status"] == "draft"]
        selected = st.selectbox(
            "Draft",
            [None] + [s["id"] for s in drafts],
            format_func=lambda i: "New draft" if i is None else f"Draft #{i}",
        )
        old = next((s for s in drafts if s["id"] == selected), {})
        zone_name = st.text_input(
            "Session timezone (IANA)",
            old.get("timezone", settings.display_timezone),
            key=f"zone_{selected}",
        )
        zone = ZoneInfo(zone_name)
        default_start = (clock.now() + timedelta(days=1)).astimezone(zone).replace(tzinfo=None)

        def local_default(field, fallback):
            return (
                utc(old[field]).astimezone(zone).replace(tzinfo=None).isoformat(timespec="minutes")
                if field in old
                else fallback.isoformat(timespec="minutes")
            )

        with st.form(f"draft_{selected}_{zone_name}"):
            course_id = st.selectbox(
                "Session course",
                [c["id"] for c in courses],
                index=next(
                    (i for i, c in enumerate(courses) if c["id"] == old.get("course_id")), 0
                ),
                format_func=lambda i: next(c["title"] for c in courses if c["id"] == i),
            )
            facilitator = st.text_input(
                "Fictitious facilitator", old.get("facilitator_name", "Demo Facilitator")
            )
            mode = st.selectbox(
                "Delivery mode",
                ["online", "in_person"],
                index=int(old.get("delivery_mode") == "in_person"),
            )
            location = st.text_input(
                "Fictitious location or demo link",
                old.get("location", "https://example.com/training"),
            )
            start = st.text_input(
                "Local start · YYYY-MM-DDTHH:MM", local_default("starts_at_utc", default_start)
            )
            end = st.text_input(
                "Local end · YYYY-MM-DDTHH:MM",
                local_default("ends_at_utc", default_start + timedelta(hours=2)),
            )
            due = st.text_input(
                "Local completion due · YYYY-MM-DDTHH:MM",
                local_default("completion_due_at_utc", default_start + timedelta(days=2)),
            )
            choices = ["Require unambiguous time", "First occurrence", "Second occurrence"]
            folds = [
                st.selectbox(f"DST occurrence for {label}", choices, key=f"fold_{label}_{selected}")
                for label in ("start", "end", "due")
            ]
            capacity = st.number_input(
                "Capacity", min_value=1, max_value=1000, value=old.get("capacity", 10), step=1
            )
            if st.form_submit_button("Save draft"):
                converted = [
                    local_to_utc(
                        datetime.fromisoformat(value),
                        zone_name,
                        None if fold == choices[0] else choices.index(fold) - 1,
                    )
                    for value, fold in zip((start, end, due), folds)
                ]
                Scheduling(settings, clock).save_draft(
                    dict(
                        zip(
                            SESSION_FIELDS,
                            (
                                course_id,
                                facilitator,
                                mode,
                                location,
                                *converted[:2],
                                zone_name,
                                int(capacity),
                                converted[2],
                            ),
                        )
                    ),
                    selected,
                )
                done("Draft saved. Review the session before publishing.")


def calendar(settings, clock, coordinator):
    st.subheader("Training calendar")
    filters = report_filters(settings, clock, "calendar_")
    status = st.selectbox("Session status", ["All", "draft", "scheduled", "completed", "cancelled"])
    selected = sessions(settings)
    department_sessions = {r["session_id"] for r in report(settings, filters, clock)["rows"]}
    selected = [
        s
        for s in selected
        if filters.start
        <= utc(s["starts_at_utc"]).astimezone(ZoneInfo(filters.timezone)).date()
        <= filters.end
        and (filters.course_id is None or s["course_id"] == filters.course_id)
        and (status == "All" or s["status"] == status)
        and (filters.department_id is None or s["id"] in department_sessions)
    ]
    table(
        [
            {
                **s,
                "local_start": utc(s["starts_at_utc"])
                .astimezone(ZoneInfo(filters.timezone))
                .isoformat(),
            }
            for s in selected
        ]
    )
    if coordinator:
        course_form(settings, clock)
        draft_form(settings, clock)
        st.markdown("### Session actions")
        sid = choose(
            "Manage session",
            sessions(settings),
            lambda r: f"#{r['id']} · {r['title']} · {r['status']}",
            "manage_session",
        )
        if sid:
            service = Scheduling(settings, clock)
            with st.form("session_actions"):
                action = st.selectbox(
                    "Action",
                    [
                        "Publish",
                        "Change capacity",
                        "Close ended session",
                        "Cancel session",
                        "Delete empty draft",
                    ],
                )
                capacity = st.number_input("New capacity", min_value=1, value=10, step=1)
                reason = st.text_input("Reason (required for cancellation or capacity change)")
                if st.form_submit_button("Apply session action"):
                    if action == "Publish":
                        service.publish(sid)
                    elif action == "Change capacity":
                        service.change_capacity(sid, int(capacity), reason)
                    elif action == "Close ended session":
                        service.close(sid)
                    elif action == "Cancel session":
                        service.cancel(sid, reason)
                    else:
                        service.delete_draft(sid)
                    done("Session updated.")


def enrollments(settings, clock, writable, role):
    st.subheader("Enrollments")
    learners = catalog(settings, "learners")
    learner_id = choose(
        "Synthetic learner",
        learners,
        lambda r: f"{r['display_name']} · {r['synthetic_employee_code']}",
        "learner",
        allow_all=role != "Learner",
    )
    sid = choose(
        "Training session",
        sessions(settings),
        lambda r: f"#{r['id']} · {r['title']} · {r['registered']}/{r['capacity']} · {r['status']}",
        "enrollment_session",
        True,
    )
    data = roster(settings, sid, learner_id)
    table(data)
    if not writable or role == "Manager":
        return
    service = Enrollment(settings, clock, role)
    with st.form("registration"):
        st.write("Registration opens only for active learners and future scheduled sessions.")
        if st.form_submit_button("Register learner"):
            if learner_id is None or sid is None:
                raise DomainError("Select a specific learner and training session to register.")
            entity_id = service.register(sid, learner_id)
            done(
                f"Registration #{entity_id} is active. Its confirmation is available in Communications."
            )
    active = [r for r in data if r["status"] == "registered"]
    if active:
        with st.form("cancel_registration"):
            eid = st.selectbox("Registration to cancel", [r["id"] for r in active])
            reason = st.text_input("Cancellation / correction reason")
            correction = (
                st.checkbox("Audited correction of an erroneous registration (Coordinator only)")
                if role == "Coordinator"
                else False
            )
            st.caption(
                "Ordinary cancellations close at the session start. An audited correction changes the current report denominator."
            )
            if st.form_submit_button("Cancel registration"):
                service.cancel(eid, reason, correction=correction)
                done(
                    "Registration cancelled; obsolete messages were cancelled and a cancellation notice was queued."
                )


def attendance(settings, clock, coordinator):
    st.subheader("Attendance & completion")
    sid = choose(
        "Session roster",
        sessions(settings),
        lambda r: f"#{r['id']} · {r['title']} · {r['status']}",
        "attendance_session",
    )
    if sid is None:
        return
    data = [r for r in roster(settings, sid) if r["status"] == "registered"]
    status = st.selectbox("Completion filter", ["All", "not_completed", "completed", "overdue"])
    filtered = [
        r
        for r in data
        if status == "All"
        or r["completion_status"] == status
        or (
            status == "overdue"
            and r["completion_status"] == "not_completed"
            and r["completion_due_at_utc"] < stamp(clock.now())
        )
    ]
    table(filtered)
    session = next(s for s in sessions(settings) if s["id"] == sid)
    st.caption(
        f"Published completion rule: {session['completion_rule_snapshot'] or 'Not published'}. Attendance and completion remain separate records."
    )
    if not coordinator or not data:
        return
    if session["status"] not in {"scheduled", "completed"} or session["ends_at_utc"] > stamp(
        clock.now()
    ):
        st.info(
            "Recording opens after this non-cancelled session ends. Use the local Demo Clock to advance a synthetic scenario."
        )
        return
    with st.form("single_attendance"):
        st.markdown("#### Record one learner")
        eid = choose(
            "Registration", data, lambda r: f"#{r['id']} · {r['display_name']}", "record_eid"
        )
        attendance_status = st.selectbox(
            "Attendance", ["unrecorded", "present", "absent", "excused"]
        )
        completion_status = st.selectbox("Completion", ["not_completed", "completed"])
        completed_at = st.text_input("Completion time (optional ISO timestamp with UTC offset)")
        reason = st.text_input("Change reason")
        if st.form_submit_button("Save learner record"):
            Completion(settings, clock).save_batch(
                sid,
                [
                    {
                        "id": eid,
                        "attendance_status": attendance_status,
                        "completion_status": completion_status,
                        "completed_at": completed_at or None,
                    }
                ],
                reason,
            )
            done("Attendance and completion saved.")
    with st.expander("Batch recording · all rows succeed or all roll back"):
        st.caption(
            "For attendance_only sessions, completion is derived from attendance. Blank completion time uses the business clock on first completion."
        )
        with st.form("batch_attendance"):
            frame = pd.DataFrame(data)[
                ["id", "display_name", "attendance_status", "completion_status", "completed_at"]
            ]
            edited = st.data_editor(
                frame,
                hide_index=True,
                disabled=["id", "display_name"],
                key=f"batch_{sid}",
                column_config={
                    "attendance_status": st.column_config.SelectboxColumn(
                        options=["unrecorded", "present", "absent", "excused"], required=True
                    ),
                    "completion_status": st.column_config.SelectboxColumn(
                        options=["not_completed", "completed"], required=True
                    ),
                    "completed_at": st.column_config.TextColumn("Completion time (UTC)"),
                },
            )
            reason = st.text_input("Batch change reason")
            if st.form_submit_button("Save entire roster"):
                Completion(settings, clock).save_batch(
                    sid, edited.where(pd.notna(edited), None).to_dict("records"), reason
                )
                done("Entire roster saved atomically.")


def communications(settings, clock, coordinator):
    st.subheader("Communications")
    st.info(
        "Simulated delivery · no email is sent. Run rules to queue reminders and overdue follow-ups, then review before processing."
    )
    jobs = catalog(settings, "communication_jobs")
    columns = st.columns(4)
    for col, state in zip(columns, ["pending", "simulated_sent", "failed", "cancelled"]):
        col.metric(state.replace("_", " ").title(), sum(j["status"] == state for j in jobs))
    state = st.selectbox(
        "Message status", ["All", "pending", "simulated_sent", "failed", "cancelled"]
    )
    filtered = [j for j in jobs if state == "All" or j["status"] == state]
    table(filtered)
    if any(j["status"] == "failed" and j["attempt_count"] >= 3 for j in jobs):
        st.warning(
            "Some messages reached the 3-attempt limit and require manual review. Retry will skip them."
        )
    if filtered:
        jid = choose(
            "Preview message",
            filtered,
            lambda r: f"#{r['id']} · {r['message_type']} · {r['recipient_snapshot']}",
            "preview_job",
        )
        job = next(j for j in filtered if j["id"] == jid)
        with st.container(border=True):
            st.text(job["subject_rendered"])
            st.text(job["body_rendered"])
            st.caption(
                f"Template #{job['template_id']} · attempt {job['attempt_count']} · {job['status']}"
            )
    if coordinator:
        service = Communications(settings, clock)
        fail_first = st.selectbox("Mock: fail the first N attempts per message", [0, 1, 2, 3])
        cols = st.columns(3)
        if cols[0].button("Run rules"):
            done(f"Rules queued {service.run_rules()} new messages.")
        if cols[1].button("Process pending (simulate)"):
            done(f"Simulated delivery: {service.process(provider=MockProvider(fail_first))}")
        if cols[2].button("Retry failed (simulate)"):
            done(
                f"Simulated retry: {service.process(retry_failed=True, provider=MockProvider(fail_first))}"
            )
        with st.expander("Template editor · new versions preserve message history"):
            kind = st.selectbox("Template type", TYPES)
            template = next(
                (
                    t
                    for t in catalog(settings, "message_templates")
                    if t["message_type"] == kind and t["active"]
                ),
                {},
            )
            with st.form(f"template_{kind}"):
                subject = st.text_input("Subject template", template.get("subject_template", ""))
                body = st.text_area("Body template", template.get("body_template", ""), height=160)
                st.caption(
                    "Allowed variables: " + ", ".join("{" + v + "}" for v in sorted(VARIABLES))
                )
                preview, save = st.columns(2)
                if preview.form_submit_button("Preview template"):
                    values = {
                        "learner": "Demo Learner",
                        "course": "Demo Course",
                        "session_date": "2026-10-26 10:00",
                        "timezone": settings.display_timezone,
                        "reason": "Demo update",
                    }
                    st.text(render(subject, values))
                    st.text(render(body, values))
                if save.form_submit_button("Save template version"):
                    service.save_template(kind, subject, body)
                    done("New template version saved; existing message snapshots are unchanged.")


def reports(settings, clock):
    st.subheader("Reports")
    st.caption(
        "Current database state grouped by session start date. The Demo Clock changes business evaluation, not historical records."
    )
    filters = report_filters(settings, clock, "report_")
    data = report(settings, filters, clock)
    summary_cards(data)
    summary = data["summary"]
    st.caption(
        f"As of {data['as_of']} · dates in {data['timezone']} · Synthetic data / Portfolio demo"
    )
    st.write(
        f"Record coverage: {ratio(summary['coverage'])} ({summary['coverage']['numerator']}/{summary['coverage']['denominator']}). Excused: {summary['excused']}. Unrecorded: {summary['unrecorded']}."
    )
    if summary["capacity"] is None:
        st.info(
            "Capacity utilization is hidden with a department filter: shared session seats are not department quotas."
        )
    else:
        value = summary["capacity"]
        st.write(
            f"Capacity utilization: {ratio(value)} ({value['numerator']}/{value['denominator']} seats). Draft and cancelled sessions are excluded."
        )
    left, right = st.columns(2)
    with left:
        st.markdown("#### Completion by department")
        chart = [
            {
                "Department": r["department"],
                "Completion rate (%)": None
                if r["completion"]["rate"] is None
                else 100 * r["completion"]["rate"],
                "Completed": r["completion"]["numerator"],
                "Ended registrations": r["completion"]["denominator"],
            }
            for r in data["groups"]["department"]
        ]
        if chart:
            st.bar_chart(
                pd.DataFrame(chart), x="Department", y="Completion rate (%)", color="#087E8B"
            )
            table(chart)
        st.caption(
            "Completed / ended active registrations. Future sessions do not enter the denominator; N/A means no ended registrations."
        )
    with right:
        st.markdown("#### Monthly registration trend")
        chart = [
            {"Month": r["month"], "Active registrations": r["registrations"]}
            for r in data["groups"]["month"]
        ]
        if chart:
            st.line_chart(pd.DataFrame(chart), x="Month", y="Active registrations", color="#087E8B")
            table(chart)
        st.caption(
            "Current active registrations grouped by session month in the displayed timezone; not registration-event history."
        )
    with st.expander("Course summary and session utilization"):
        table(
            [
                {
                    "Course": r["course"],
                    "Registrations": r["registrations"],
                    "Completed": r["completion"]["numerator"],
                    "Ended registrations": r["completion"]["denominator"],
                    "Completion rate": ratio(r["completion"]),
                }
                for r in data["groups"]["course"]
            ]
        )
        table(data["sessions"])
    st.markdown("### Report detail")
    st.caption(
        "Includes cancelled records for reconciliation; they are excluded from active-rate denominators. This table and the CSV use the same filtered rows."
    )
    table(data["rows"])
    st.download_button(
        "Download filtered CSV",
        export_csv(data["rows"]),
        "learnops-synthetic-report.csv",
        "text/csv",
    )


def main():
    st.set_page_config(page_title="LearnOps Flow", page_icon="◈", layout="wide")
    try:
        settings = Settings.from_env()
        st.sidebar.title("LearnOps Flow")
        st.sidebar.caption("LEARNING OPERATIONS")
        area = st.sidebar.radio("Workspace", AREAS, key="area")
        role = st.sidebar.selectbox(
            "Demo role — no authentication", ["Coordinator", "Learner", "Manager"], key="role"
        )
        writable = settings.app_mode == "local_demo"
        st.sidebar.caption("Local writable demo" if writable else "Public read-only demo")
        if writable:
            with st.sidebar.form("clock_form"):
                value = st.text_input(
                    "Demo Clock (ISO time with offset)",
                    st.session_state.get("clock_value", settings.demo_as_of),
                )
                if st.form_submit_button("Set Demo Clock"):
                    st.session_state["clock_value"] = stamp(utc(value))
                    done(
                        "Demo Clock updated. Reports show current state, not a historical snapshot."
                    )
        clock = FixedClock(
            utc(
                st.session_state.get("clock_value", settings.demo_as_of)
                if writable
                else settings.demo_as_of
            )
        )
        st.sidebar.divider()
        st.sidebar.caption(f"Business clock: {stamp(clock.now())}")
        st.sidebar.caption(f"Display timezone: {settings.display_timezone}")
        st.sidebar.caption(
            "Synthetic data only. No real identities, authentication, or message delivery."
        )
        st.title("LearnOps Flow")
        st.caption("SYNTHETIC DATA / PORTFOLIO DEMO · Learning Operations Automation Platform")
        if "notice" in st.session_state:
            st.success(st.session_state.pop("notice"))
        coordinator = writable and role == "Coordinator"
        if area == "Overview":
            overview(settings, clock)
        elif area == "Training calendar":
            calendar(settings, clock, coordinator)
        elif area == "Enrollments":
            enrollments(settings, clock, writable, role)
        elif area == "Attendance & completion":
            attendance(settings, clock, coordinator)
        elif area == "Communications":
            communications(settings, clock, coordinator)
        elif area == "Reports":
            reports(settings, clock)
        else:
            st.subheader("Audit trail")
            st.caption(
                "Demo roles are labels, not verified identities. System operation time and business evaluation time are recorded separately."
            )
            table(list(reversed(catalog(settings, "audit_events"))))
    except (DomainError, ValueError, KeyError) as exc:
        st.error(str(exc))
