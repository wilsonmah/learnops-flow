# Public read-only demo preparation

Status: **preparation only; no public deployment has been performed.** All names, email addresses, sessions and records are synthetic. Do not use real employee data. This prototype has no authentication and role labels are not security controls. Public users can inspect the complete synthetic dataset and logs.

## Prepare a fresh database

Run once in a trusted build environment with the application stopped. Use Python 3.12 and install the locked requirements as described in the README. These commands create a new database exclusively and refuse to overwrite any existing file:

```powershell
$env:APP_MODE = 'local_demo'
python -m scripts.prepare_public_demo --database data/public-demo.sqlite3 --seed 42 --base-date 2026-10-25
```

The command uses the same migrations, synthetic generator and mock provider as the local demo, checks database integrity and foreign keys, and requires `APP_MODE=local_demo`. It does not start a server, connect to email, or publish anything. If preparation is interrupted, retain and inspect the incomplete file; explicitly select a new path or remove only that known disposable file yourself before retrying.

## Preview as a public visitor, locally

```powershell
$env:APP_MODE = 'public_readonly'
$env:DATABASE_PATH = 'data/public-demo.sqlite3'
$env:DISPLAY_TIMEZONE = 'America/Toronto'
$env:MESSAGE_PROVIDER = 'mock'
$env:DEMO_AS_OF = '2026-10-25T14:00:00Z'
python -m streamlit run app.py --server.address=127.0.0.1 --server.port=8502
```

Open `http://127.0.0.1:8502`. Public mode opens SQLite in read-only mode, rejects service writes and does not offer write forms, queue execution, imports, reset or clock changes. The operator must rebuild the database before exposing the app; never point public mode at a writable local demo that might contain unreviewed free-text input. The clock is fixed for reproducible interpretation and does not reconstruct historical snapshots.

For macOS/Linux, use equivalent `export` statements. Before any future deployment, separately review the hosting provider's current Python support and instructions, build a fresh synthetic database in a trusted startup/build step, ensure the application process uses `public_readonly`, verify no visitor write access, and confirm the host's ephemeral storage implications. Do not expose the writable instance or promise database persistence. Deployment, provider selection, billing and permissions require separate authorization. No demo URL is claimed here.

## Remaining review

Use the full script in [demo_script.md](demo_script.md) against a separate local writable synthetic database. Recheck public views, keyboard navigation, focus, chart alternatives and color contrast in an actual browser before public release; these steps do not imply formal accessibility certification. See [validation.md](validation.md) for what was actually checked.
