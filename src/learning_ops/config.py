import os
from dataclasses import dataclass
from pathlib import Path
from zoneinfo import ZoneInfo


class DomainError(ValueError):
    """An actionable business validation error."""


@dataclass(frozen=True)
class Settings:
    database_path: Path = Path("data/demo.sqlite3")
    app_mode: str = "public_readonly"
    display_timezone: str = "America/Toronto"
    message_provider: str = "mock"
    demo_as_of: str = "2026-10-25T14:00:00Z"

    def __post_init__(self):
        if self.app_mode not in {"local_demo", "public_readonly"}:
            raise DomainError("APP_MODE must be local_demo or public_readonly.")
        if self.message_provider != "mock":
            raise DomainError("Only mock delivery is supported.")
        ZoneInfo(self.display_timezone)

    def require_write(self):
        if self.app_mode != "local_demo":
            raise DomainError("Public demo is read-only. Use APP_MODE=local_demo locally.")

    @classmethod
    def from_env(cls):
        return cls(
            Path(os.getenv("DATABASE_PATH", "data/demo.sqlite3")),
            os.getenv("APP_MODE", "public_readonly"),
            os.getenv("DISPLAY_TIMEZONE", "America/Toronto"),
            os.getenv("MESSAGE_PROVIDER", "mock"),
            os.getenv("DEMO_AS_OF", "2026-10-25T14:00:00Z"),
        )
