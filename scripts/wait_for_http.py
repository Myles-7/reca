"""Bounded, dependency-free HTTP readiness wait used by CI smoke checks."""

from __future__ import annotations

import argparse
import http.client
import sys
import time
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("url")
    parser.add_argument("--expected-status", type=int, default=200)
    parser.add_argument("--timeout", type=float, default=90)
    parser.add_argument("--request-timeout", type=float, default=3)
    parser.add_argument("--interval", type=float, default=1)
    args = parser.parse_args()
    deadline = time.monotonic() + args.timeout
    last_error = "no request attempted"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(
                args.url, timeout=args.request_timeout
            ) as response:
                if response.status == args.expected_status:
                    print(f"ready: {args.url}")
                    return 0
                last_error = f"unexpected HTTP status {response.status}"
        except (
            urllib.error.HTTPError,
            urllib.error.URLError,
            TimeoutError,
            OSError,
            http.client.HTTPException,
        ) as error:
            last_error = f"{type(error).__name__}"
        time.sleep(args.interval)
    print(f"timed out waiting for {args.url}: {last_error}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
