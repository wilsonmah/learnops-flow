# Metric definitions

All values describe **synthetic data / portfolio demo**, at an explicit as-of, using current states. Unit: enrollment record; distinct learners is separate. One learner in two sessions contributes two enrollments.

Dates apply to session start in DISPLAY_TIMEZONE, with start included and midnight after end excluded, including 23/25-hour days. Course and registration-department-snapshot filters apply to the same detail used by charts/CSV. Cancelled detail is retained for reconciliation.

| Set | Definition |
|---|---|
| R | Active registrations in scheduled/completed sessions in the range |
| E | R with session end at or before as-of |
| P | E with attendance present |
| C | E with completion completed |
| D | E whose due time is strictly before as-of and completion is not_completed |

| Metric | Numerator | Denominator |
|---|---|---|
| Attendance | P | E |
| Completion | C | E |
| Overdue incomplete | D | E with due time strictly before as-of |
| Coverage | E with attendance other than unrecorded | E |
| Utilization | R | Sum of scheduled/completed session capacity, including empty sessions |

Zero denominators display N/A. Excused/unrecorded stay in E; unrecorded is not explicit absence. Do not average session percentages. Department filters hide capacity rates because seats are shared, not a departmental allocation.

The independent fixture in `tests/test_reporting.py` yields attendance 6/8, completion 5/8, overdue 3/8, coverage 7/8 and utilization 8/10. A future session with two registrations/capacity four changes R to 10 and utilization to 10/14, leaving ended rates unchanged. Cancelled records/sessions are excluded from active sets. Changing one present/completed learner to excused/not_completed keeps E at eight and reduces the numerators.

Monthly trend is current registrations grouped by session month, not historical signup events. Departments are snapshotted at registration and refreshed at re-registration. Late completion means completed_at is strictly after due_at. CSV has stable headers, as-of, timezone and synthetic-data source, encoded UTF-8 with BOM. Dangerous formula prefixes receive a leading apostrophe; the UI table-download route is also protected.
