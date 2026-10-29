from pathlib import Path

from streamlit.testing.v1 import AppTest

from tests.conftest import rows

APP = str(Path(__file__).resolve().parents[1] / "app.py")


def widget(elements, label):
    return next(e for e in elements if e.label == label)


def test_public_pages_no_writes_and_persistence(env, monkeypatch):
    env.session()
    monkeypatch.setenv("DATABASE_PATH", str(env.settings.database_path))
    monkeypatch.setenv("APP_MODE", "public_readonly")
    before = env.settings.database_path.read_bytes()
    app = AppTest.from_file(APP, default_timeout=20).run()
    for area in [
        "Overview",
        "Training calendar",
        "Enrollments",
        "Attendance & completion",
        "Communications",
        "Reports",
        "Audit trail",
    ]:
        app.radio(key="area").set_value(area).run()
        assert not app.exception
        assert not app.error
        assert not app.button
        assert not app.text_input
    app.run()
    assert env.settings.database_path.read_bytes() == before
    restarted = AppTest.from_file(APP, default_timeout=20).run()
    assert not restarted.exception
    assert rows(env, "sessions")[0]["id"] == 1


def test_ui_registration_clock_attendance_and_communication_path(env, monkeypatch):
    sid = env.session()
    monkeypatch.setenv("DATABASE_PATH", str(env.settings.database_path))
    monkeypatch.setenv("APP_MODE", "local_demo")
    monkeypatch.setenv("DEMO_AS_OF", "2026-10-20T14:00:00Z")
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="area").set_value("Enrollments").run()
    app.selectbox(key="learner").set_value(1)
    app.selectbox(key="enrollment_session").set_value(sid).run()
    widget(app.button, "Register learner").click().run()
    assert not app.exception and not app.error
    assert len(rows(env, "enrollments")) == 1
    widget(app.button, "Register learner").click().run()
    assert len(rows(env, "enrollments")) == 1
    app.radio(key="area").set_value("Communications").run()
    widget(app.button, "Process pending (simulate)").click().run()
    assert rows(env, "communication_jobs")[0]["status"] == "simulated_sent"
    widget(app.text_input, "Demo Clock (ISO time with offset)").set_value("2026-10-25T17:00:00Z")
    widget(app.button, "Set Demo Clock").click().run()
    app.radio(key="area").set_value("Attendance & completion").run()
    widget(app.selectbox, "Attendance").set_value("present")
    widget(app.selectbox, "Completion").set_value("completed")
    widget(app.button, "Save learner record").click().run()
    assert not app.exception and not app.error
    assert rows(env, "enrollments")[0]["completion_status"] == "completed"
    app.radio(key="area").set_value("Reports").run()
    assert not app.exception and not app.error
    assert any(m.label == "Completion rate" and m.value == "100.0%" for m in app.metric)


def test_missing_database_is_actionable(tmp_path, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(tmp_path / "missing.sqlite3"))
    monkeypatch.setenv("APP_MODE", "public_readonly")
    app = AppTest.from_file(APP).run()
    assert not app.exception
    assert "not initialized" in app.error[0].value


def test_ui_create_and_publish_draft(env, monkeypatch):
    monkeypatch.setenv("DATABASE_PATH", str(env.settings.database_path))
    monkeypatch.setenv("APP_MODE", "local_demo")
    monkeypatch.setenv("DEMO_AS_OF", "2026-10-20T14:00:00Z")
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="area").set_value("Training calendar").run()
    widget(app.button, "Save draft").click().run()
    assert not app.exception and not app.error
    assert rows(env, "sessions")[0]["status"] == "draft"
    widget(app.button, "Apply session action").click().run()
    assert not app.exception and not app.error
    assert rows(env, "sessions")[0]["status"] == "scheduled"
    widget(app.selectbox, "Action").set_value("Change capacity")
    widget(app.number_input, "New capacity").set_value(12)
    widget(app.text_input, "Reason (required for cancellation or capacity change)").set_value(
        "Demo adjustment"
    )
    widget(app.button, "Apply session action").click().run()
    assert not app.exception and not app.error
    assert rows(env, "sessions")[0]["capacity"] == 12


def test_builtin_dataframe_export_is_sanitized(env, monkeypatch):
    env.session()
    env.schedule.save_course(
        "=DangerousTitle", "Core", "Synthetic", "attendance_only", course_id=env.course
    )
    monkeypatch.setenv("DATABASE_PATH", str(env.settings.database_path))
    monkeypatch.setenv("APP_MODE", "public_readonly")
    app = AppTest.from_file(APP, default_timeout=20).run()
    app.radio(key="area").set_value("Training calendar").run()
    assert app.dataframe[0].value["title"].iloc[0] == "'=DangerousTitle"
