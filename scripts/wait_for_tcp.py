"""Wait until a TCP host:port accepts connections (used for local dev / health gates)."""

from __future__ import annotations

import argparse
import socket
import sys
import time


def wait_for_tcp(host: str, port: int, timeout_s: float = 120.0, interval_s: float = 1.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=3):
                return True
        except OSError:
            time.sleep(interval_s)
    return False


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("host")
    p.add_argument("port", type=int)
    p.add_argument("--timeout", type=float, default=120.0)
    p.add_argument("--interval", type=float, default=1.0)
    args = p.parse_args()
    ok = wait_for_tcp(args.host, args.port, timeout_s=args.timeout, interval_s=args.interval)
    sys.exit(0 if ok else 2)


if __name__ == "__main__":
    main()
