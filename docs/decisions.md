# Decisions — 2026-10-25 local batch

- Started from remote main `f383f68fe2384ef1824d8903612cd9041fb4e9e2` in this task's checkout. No earlier application existed. The owner subsequently authorized synchronization of the implementation and English specification.
- Keep Python + Streamlit + SQLite. Use verified Python 3.12.14 rather than host Python 3.15. Pinned versions are a validated combination, not a claim of latest versions.
- Seven views share `learning_ops.ui.app` instead of separate Streamlit page files, keeping mode/role/clock setup consistent. Business logic is separate and independently tested.
- Package migrations with the Python module, enabling installed-package initialization. Execute migration statements individually in a transaction; sqlite3 executescript implicitly commits existing transactions.
- Use direct DB-API and BEGIN IMMEDIATE; no ORM, API server or worker is needed for this scope.
- Default public read-only and fixed as-of; environment configuration is explicit. `.env.example` is documentation, not an implicit loader.
- Published details lock. Course title remains a live catalog label; the completion rule is snapshotted as required. Rescheduling uses cancellation and a new session.
- An explicit Coordinator demo correction handles erroneous post-start registrations with a required reason and distinct audit action. It changes current denominators and is not production authorization.
- Batch recording is atomic. No optimistic edit versioning: assume single-user local operation; evaluate conflicts before multi-user use.
- Seed through real services with short transactions. The full sequence is not globally atomic; interrupted seeding requires explicit reset. Logical seed data is deterministic, actual audit operation time is not.
- Browser inspection exposed Streamlit's additional CSV download path. Protect both custom exports and dataframe input; add regression coverage.
- Pin transitive dependencies via constraints. Linux/Python 3.12 CI is configured but not claimed to have run remotely.
- No license, real delivery/identities, deployment or business outcomes were added. The owner reviewed the local version; future batches still require separate GitHub authorization.
