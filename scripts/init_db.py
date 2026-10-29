from learning_ops.config import Settings
from learning_ops.db import initialize


def main():
    settings = Settings.from_env()
    initialize(settings)
    print(f"Initialized {settings.database_path}; schema version 1.")


if __name__ == "__main__":
    main()
