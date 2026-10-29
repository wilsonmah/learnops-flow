import argparse

from learning_ops.clock import FixedClock, utc
from learning_ops.config import Settings
from learning_ops.services.communications import Communications, MockProvider


def main():
    parser = argparse.ArgumentParser(description="One rule scan and one simulated delivery pass.")
    parser.add_argument("--as-of", required=True)
    parser.add_argument("--mode", choices=["mock"], default="mock")
    parser.add_argument("--retry-failed", action="store_true")
    parser.add_argument("--fail-first", type=int, choices=range(4), default=0)
    args = parser.parse_args()
    service = Communications(Settings.from_env(), FixedClock(utc(args.as_of)))
    print(
        {
            "queued": service.run_rules(),
            "delivery": service.process(
                retry_failed=args.retry_failed, provider=MockProvider(args.fail_first)
            ),
        }
    )


if __name__ == "__main__":
    main()
