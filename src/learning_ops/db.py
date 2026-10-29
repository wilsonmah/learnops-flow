import sqlite3
from contextlib import contextmanager
from importlib.resources import files

from learning_ops.clock import SystemClock, stamp
from learning_ops.config import DomainError, Settings


@contextmanager
def connect(settings: Settings, *, write=False, create=False):
    if write or create:
        settings.require_write()
    path = settings.database_path.resolve()
    if create:
        path.parent.mkdir(parents=True, exist_ok=True)
    mode = "rwc" if create else ("rw" if write else "ro")
    conn = None
    try:
        conn = sqlite3.connect(
            path.as_uri() + f"?mode={mode}", uri=True, timeout=5, isolation_level=None
        )
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("BEGIN IMMEDIATE" if write else "BEGIN")
        yield conn
        conn.commit()
    except sqlite3.OperationalError as exc:
        if conn:
            conn.rollback()
        if "locked" in str(exc):
            raise DomainError("Database is busy. Please retry in a few seconds.") from exc
        if "unable to open" in str(exc) or "no such table" in str(exc):
            raise DomainError(
                "Database is not initialized. Run scripts.init_db and scripts.seed_demo locally."
            ) from exc
        raise
    except BaseException:
        if conn:
            conn.rollback()
        raise
    finally:
        if conn:
            conn.close()


def initialize(settings: Settings):
    with connect(settings, write=True, create=True) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS schema_migrations (version INTEGER PRIMARY KEY, applied_at_utc TEXT NOT NULL)"
        )
        for migration in sorted(
            files("learning_ops").joinpath("migrations").iterdir(), key=lambda p: p.name
        ):
            version = int(migration.name.split("_")[0])
            if conn.execute(
                "SELECT 1 FROM schema_migrations WHERE version=?", (version,)
            ).fetchone():
                continue
            # Execute individually: executescript would implicitly commit the transaction.
            for statement in migration.read_text(encoding="utf-8").split(";"):
                if statement.strip():
                    conn.execute(statement)
            conn.execute(
                "INSERT INTO schema_migrations VALUES (?,?)", (version, stamp(SystemClock().now()))
            )
