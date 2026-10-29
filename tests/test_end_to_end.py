from datetime import date

from learning_ops.clock import utc
from learning_ops.reporting import Filters, export_csv, report
from learning_ops.services.communications import MockProvider
from tests.conftest import rows


def test_complete_local_demo_scenario(env):
    sid = env.session(capacity=10)
    first, second = [env.enrollment.register(sid, i) for i in (1, 2)]
    env.schedule.change_capacity(sid, 2, "Small demo group")
    env.enrollment.cancel(second, "Demo schedule conflict")
    assert env.enrollment.register(sid, 2) == second
    env.clock.value = utc("2026-10-24T14:00:00Z")
    assert env.comm.run_rules() == 2
    assert env.comm.run_rules() == 0
    assert env.comm.process(provider=MockProvider(1))["failed"] == 4
    assert env.comm.process(retry_failed=True)["simulated_sent"] == 4
    env.clock.value = utc("2026-10-25T17:00:00Z")
    env.completion.save_batch(
        sid,
        [
            {"id": first, "attendance_status": "present", "completion_status": "completed"},
            {"id": second, "attendance_status": "present", "completion_status": "not_completed"},
        ],
    )
    env.schedule.close(sid)
    env.clock.value = utc("2026-10-27T14:00:00Z")
    assert env.comm.run_rules() == 1
    assert env.comm.run_rules() == 0
    env.comm.process()
    data = report(env.settings, Filters(date(2026, 10, 25), date(2026, 10, 25)), env.clock)
    summary = data["summary"]
    assert (
        summary["attendance"]["rate"]
        == summary["capacity"]["rate"]
        == summary["coverage"]["rate"]
        == 1
    )
    assert summary["completion"]["rate"] == summary["overdue"]["rate"] == 0.5
    assert len(data["rows"]) == 2
    assert "Synthetic data / Portfolio demo" in export_csv(data["rows"]).decode("utf-8-sig")
    assert {j["message_type"] for j in rows(env, "communication_jobs")} == {
        "confirmation",
        "reminder",
        "cancellation",
        "completion",
        "followup",
    }
    assert all(a["occurred_at_utc"] and a["business_as_of_utc"] for a in rows(env, "audit_events"))
