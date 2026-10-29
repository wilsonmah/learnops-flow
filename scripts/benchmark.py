"""Warm query timings on the configured synthetic database; never writes business data."""

import json
import platform
import sqlite3
import statistics
from datetime import date
from time import perf_counter

from learning_ops.clock import FixedClock, utc
from learning_ops.config import Settings
from learning_ops.reporting import Filters, export_csv, report
from learning_ops.repository import catalog, roster, sessions


def main():
    settings = Settings.from_env()
    clock = FixedClock(utc(settings.demo_as_of))
    filters = Filters(date(2000, 1, 1), date(2100, 1, 1), settings.display_timezone)
    operations = {
        "calendar": lambda: sessions(settings),
        "roster": lambda: roster(settings),
        "report": lambda: report(settings, filters, clock),
        "report_and_csv": lambda: export_csv(report(settings, filters, clock)["rows"]),
        "communication_log": lambda: catalog(settings, "communication_jobs"),
    }
    output = {
        "platform": platform.platform(),
        "python": platform.python_version(),
        "sqlite": sqlite3.sqlite_version,
        "processor": platform.processor(),
        "business_as_of": settings.demo_as_of,
        "counts": {
            "learners": len(catalog(settings, "learners")),
            "sessions": len(sessions(settings)),
            "enrollments": len(roster(settings)),
        },
        "measurement": "One warmup then 10 calls per query. Wall-clock seconds; excludes UI/browser rendering. Local synthetic data only.",
        "results": {},
    }
    for name, call in operations.items():
        call()
        timings = []
        for _ in range(10):
            start = perf_counter()
            call()
            timings.append(perf_counter() - start)
        output["results"][name] = {
            "median_seconds": statistics.median(timings),
            "max_seconds": max(timings),
            "samples_seconds": timings,
        }
    print(json.dumps(output, indent=2))


if __name__ == "__main__":
    main()
