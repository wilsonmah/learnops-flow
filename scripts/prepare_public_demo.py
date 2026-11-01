"""Explicitly build a new synthetic database before starting a read-only demo."""

import argparse
from datetime import date
from pathlib import Path

from learning_ops.config import Settings
from learning_ops.db import connect, initialize
from learning_ops.seed import seed_demo


def prepare(path: Path, seed: int, base_date: date):
    Settings.from_env().require_write()
    path = path.resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive creation prevents overwriting a user's existing database.
    with path.open("xb"):
        pass
    settings = Settings(path, "local_demo")
    initialize(settings)
    result = seed_demo(settings, seed, base_date)
    with connect(settings) as conn:
        if conn.execute("PRAGMA integrity_check").fetchone()[0] != "ok":
            raise RuntimeError("Synthetic database integrity check failed.")
        if conn.execute("PRAGMA foreign_key_check").fetchone():
            raise RuntimeError("Synthetic database foreign-key check failed.")
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("data/public-demo.sqlite3"))
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-date", type=date.fromisoformat, default=date(2026, 10, 25))
    args = parser.parse_args()
    result = prepare(args.database, args.seed, args.base_date)
    print(f"Prepared {args.database}: {result}")
    print(f"Use APP_MODE=public_readonly and DEMO_AS_OF={args.base_date}T14:00:00Z")


if __name__ == "__main__":
    main()
