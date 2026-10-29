import argparse
from datetime import date

from learning_ops.config import Settings
from learning_ops.seed import seed_demo


def main():
    parser = argparse.ArgumentParser(
        description="Seed synthetic portfolio data; refuses existing data."
    )
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--base-date", type=date.fromisoformat, required=True)
    args = parser.parse_args()
    print(seed_demo(Settings.from_env(), args.seed, args.base_date))


if __name__ == "__main__":
    main()
