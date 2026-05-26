"""Monitor a Kaggle kernel until COMPLETE or ERROR."""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import time


def kaggle_status(kernel: str) -> str:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    result = subprocess.run(
        ["kaggle", "kernels", "status", kernel],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "status command failed")
    return result.stdout.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kernel", help="<owner>/<slug>")
    parser.add_argument("--interval", type=int, default=60)
    parser.add_argument("--timeout", type=int, default=6 * 60 * 60)
    parser.add_argument("--once", action="store_true")
    args = parser.parse_args()

    start = time.time()
    while True:
        status = kaggle_status(args.kernel)
        elapsed = int(time.time() - start)
        print(f"[{elapsed:>5}s] {status}", flush=True)
        if "KernelWorkerStatus.COMPLETE" in status:
            return 0
        if "KernelWorkerStatus.ERROR" in status:
            return 1
        if args.once:
            return 0
        if elapsed >= args.timeout:
            print("timeout while waiting for terminal status")
            return 2
        time.sleep(max(1, args.interval))


if __name__ == "__main__":
    sys.exit(main())

