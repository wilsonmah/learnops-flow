# 3–5 minute demonstration

Prepare a fresh seed, local mode and business clock `2026-10-25T14:00:00Z`. All records are fictional. Rehearsal takes longer; pre-create the workshop and two registrations for a short narrated recording.

## 0:00–0:40 — Context

Show Overview: schedules, rosters, attendance, follow-ups and reporting use one source of truth. Point to Synthetic data / Portfolio demo and Demo role — no authentication. Explain simulated processing accurately.

## 0:40–1:40 — Schedule and enroll

1. Create `Demo Support Workshop`, completion rule `attendance_plus_confirmation`, in Training calendar.
2. Create a draft: that course, fictional facilitator/location, America/Toronto, start `2026-10-26T10:00`, end `2026-10-26T12:00`, due `2026-10-27T12:00`, capacity 10. Save and publish via Session actions. Note the ID (25 after a fresh seed).
3. In Enrollments select the session and Demo Learner 001; register twice to show one record/confirmation. Register Demo Learner 002.
4. Reduce capacity to two with reason `Small demo group`; attempt Learner 003 and show the full-session error. Automated testing also covers concurrent competition for one seat.
5. Optional: cancel/re-register Learner 002 before start; show cycle 2, released capacity and obsolete cancelled messages.

## 1:40–2:40 — Communications and completion

1. Preview a new confirmation. At the initial clock, the workshop is exactly 24 hours away. Run rules twice: the second run adds no duplicates.
2. Select mock failure count 1 and Process pending. Show failed/attempt count. Select zero and Retry failed; success says simulated_sent. Total maximum is three attempts.
3. Set Demo Clock to `2026-10-26T17:00:00Z`. Open the workshop roster after its end.
4. Save Learner 001 present/completed, Learner 002 present/not_completed. The batch editor saves the whole roster atomically; later corrections require reasons.

## 2:40–3:40 — Follow-up and reporting

1. Set Demo Clock to `2026-10-28T14:00:00Z`. Run rules and preview Learner 002's follow-up; rerun to show deduplication.
2. Filter Reports to the workshop. Expected: two active registrations, attendance 2/2, completion 1/2, overdue 1/2, coverage 2/2 and capacity 2/2 after the capacity adjustment.
3. Show detail and Download filtered CSV. Department filtering hides utilization because shared seats are not department quotas.

## 3:40–5:00 — Evidence and limits

Show audit before/after values, reasons and system/business timestamps. Explain the write lock, cycle/revision keys and fixed metric fixture. Point to validation evidence.

State the limits: synthetic data, no real authentication/delivery, no public deployment, no historical snapshots and no measured organizational outcomes. Restart preserves data; reset is an explicit local command after stopping the app.
