# Local validation record

## Context

- Implementation based on repository main `f383f68fe2384ef1824d8903612cd9041fb4e9e2`. At validation time these changes were local and uncommitted; consult Git history for their subsequent synchronization.
- Windows 11 build 26300, Python 3.12.14, SQLite 3.53.1. Business as-of `2026-10-25T14:00:00Z`; seed 42, base date 2026-10-25. Synthetic data only.
- Independent clean-directory validation: installation and initialization performed on 2026-10-25; test and lint checks repeated on 2026-10-29. The independent directory used its own Python virtual environment and database.

## Actual checks

| Check | Result |
|---|---|
| `python -m pip install -r requirements-dev.txt` and `python -m pip install -e . --no-deps` | Successful in independent virtual environment; dependencies retrieved from configured package registry/cache |
| `python -m pip check` | No broken requirements |
| `python -m scripts.init_db` and `python -m scripts.seed_demo --seed 42 --base-date 2026-10-25` | Successful; 200 learners, 6 departments, 8 courses, 24 sessions, 408 registrations |
| `python -m pytest -q` | 38 passed in 30.80 seconds in independent environment |
| `python -m ruff check .` and `python -m ruff format --check .` | Passed; 29 files formatted |
| `python -m scripts.run_communications --as-of 2026-10-25T14:00:00Z --mode mock` | Successful single run; zero newly queued and zero pending to process in the existing clean database |
| Local Streamlit browser and health endpoint | Overview and reporting charts visually inspected on 2026-10-25; health endpoint returned `ok` on 2026-10-29. AppTest exercises local registration, mock delivery, recording, reports, draft publishing and read-only pages |
| Fixed metrics fixture | Attendance 6/8, completion 5/8, overdue 3/8, coverage 7/8, utilization 8/10; future-session and empty-set checks passed |
| Concurrent last seat, rollback, deduplication, retries, read-only writes, DST and CSV | Covered by passing automated tests |

The first virtual-environment creation encountered a restricted temporary-directory permission error; pointing TEMP/TMP at a writable task-local folder allowed setup to succeed. An initial sandboxed local-server attempt could not bind; the local-only server was subsequently started and verified. A browser automation attempt to press an arrow key timed out; keyboard navigation has not been verified. Initial dataframe deprecation warnings were addressed before the final checks.

## Performance

On 2026-10-25, one warmup followed by ten measured calls per operation on this machine and seed yielded the following wall-clock times. See `benchmark.json` for all samples and environment details. These numbers exclude browser rendering and do not establish a cloud SLA or real-world efficiency gain.

| Operation | Median seconds | Maximum seconds |
|---|---:|---:|
| Calendar query | 0.0063 | 0.0073 |
| Roster query | 0.0118 | 0.0131 |
| Report query | 0.0331 | 0.0384 |
| Report plus CSV | 0.0469 | 0.0547 |
| Communication log | 0.0181 | 0.0357 |

## Limitations and remaining checks

- No remote CI run, deployment, cross-platform execution, comprehensive accessibility review or successful keyboard-navigation check is claimed. No user acceptance review or complete timed 3–5 minute manual walkthrough has been performed.
- The tests and browser checks cover the main paths, but do not prove every possible UI interaction or production suitability.
- No true authentication, production authorization, real message delivery, historic snapshots, multi-instance scheduling or optimistic edit-conflict protection. Local demo role labels are not security boundaries. Free-text inputs are intended for fictional content but do not automatically detect real personal data.
- Public mode requires an already initialized synthetic database. Seed uses multiple transactions and interrupted generation requires the explicit reset process.
- The results demonstrate local synthetic scenarios only. No real organization, business benefit, employee usage, or efficiency improvement was measured.
