"""Pull and scan Kaggle kernel logs, or scan an existing local log."""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path


DEFAULT_MARKERS = [
    ("Traceback", "FATAL", "Python exception"),
    ("RuntimeError", "FATAL", "runtime error"),
    ("FileNotFoundError", "FATAL", "missing file or asset"),
    ("KeyError", "FATAL", "missing key or column"),
    ("CUDA out of memory", "FATAL", "GPU OOM"),
    ("Killed", "FATAL", "process killed, likely OOM"),
    ("Notebook Timeout", "FATAL", "sandbox timeout"),
    ("row/column mismatch", "FATAL", "submission shape mismatch"),
    ("DeprecationWarning", "INFO", "dependency warning"),
    ("UserWarning", "INFO", "user warning"),
]


def kaggle_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    return subprocess.run(
        ["kaggle", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
    )


def load_markers(path: Path | None) -> list[tuple[str, str, str]]:
    if path is None:
        return DEFAULT_MARKERS
    data = json.loads(path.read_text(encoding="utf-8"))
    return [(str(row[0]), str(row[1]), str(row[2])) for row in data]


def pull_log(kernel: str, out_dir: Path, version: str | None) -> Path:
    status = kaggle_cmd("kernels", "status", kernel)
    print(f"## status: {status.stdout.strip() or status.stderr.strip()}")
    if status.returncode != 0:
        raise SystemExit(status.stderr.strip() or "failed to query kernel status")
    if "COMPLETE" not in status.stdout and "ERROR" not in status.stdout:
        raise SystemExit("kernel is not terminal yet; wait for COMPLETE or ERROR")

    out_dir.mkdir(parents=True, exist_ok=True)
    args = ["kernels", "output", kernel, "-p", str(out_dir)]
    if version:
        args.extend(["--version", version])
    output = kaggle_cmd(*args)
    if output.returncode != 0:
        raise SystemExit(output.stderr.strip() or "failed to pull kernel output")

    log = next(out_dir.glob("*.log"), None)
    if log is None:
        raise SystemExit(f"no .log file found in {out_dir}")
    return log


def scan_log(log_path: Path, markers: list[tuple[str, str, str]]) -> int:
    text = log_path.read_text(encoding="utf-8", errors="replace")
    fatal_count = 0
    print(f"## scanning: {log_path}")
    for needle, severity, meaning in markers:
        count = text.count(needle)
        if not count:
            continue
        print(f"[{severity}] x{count} {needle!r} -> {meaning}")
        if "FATAL" in severity:
            fatal_count += count
            idx = text.find(needle)
            snippet = text[idx : idx + 300].replace("\n", " | ")
            print(f"  first hit: {snippet[:280]}")

    if fatal_count:
        print(f"## verdict: BAD ({fatal_count} fatal marker hits)")
        return 1
    print("## verdict: OK (no fatal markers)")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("kernel", nargs="?", help="<owner>/<slug>; omit when --log is used")
    parser.add_argument("out_dir", nargs="?", type=Path, help="Output directory for pulled kernel artifacts")
    parser.add_argument("--version", help="Specific Kaggle kernel version")
    parser.add_argument("--log", type=Path, help="Scan an existing local log instead of pulling output")
    parser.add_argument("--markers", type=Path, help="JSON list of [needle,severity,meaning]")
    args = parser.parse_args()

    markers = load_markers(args.markers)
    if args.log:
        return scan_log(args.log, markers)
    if not args.kernel or not args.out_dir:
        raise SystemExit("usage: verify_kernel_log.py <kernel> <out_dir> or --log <path>")
    log = pull_log(args.kernel, args.out_dir, args.version)
    return scan_log(log, markers)


if __name__ == "__main__":
    sys.exit(main())

