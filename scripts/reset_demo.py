import argparse
from datetime import date

from learning_ops.config import DomainError, Settings
from learning_ops.db import connect, initialize
from learning_ops.seed import seed_demo


def main():
    parser = argparse.ArgumentParser(
        description="Stop the app first. Reset only the configured synthetic demo database."
    )
    parser.add_argument("--confirm-reset", action="store_true", required=True)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    settings = Settings.from_env()
    settings.require_write()
    with connect(settings, write=True) as conn:
        marker = conn.execute("SELECT value FROM demo_metadata WHERE key='source'").fetchone()
        if not marker or marker[0] != "Synthetic data / Portfolio demo":
            raise DomainError("Refusing to reset a database without the synthetic demo marker.")
        for table in (
            "communication_jobs",
            "audit_events",
            "enrollments",
            "sessions",
            "courses",
            "learners",
            "departments",
            "message_templates",
            "demo_metadata",
        ):
            conn.execute(f"DELETE FROM {table}")
    initialize(settings)
    print(seed_demo(settings, args.seed, args.base_date))


if __name__ == "__main__":
    main()
