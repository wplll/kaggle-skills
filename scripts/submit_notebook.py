"""Validate and submit a completed Kaggle notebook version to a code competition.

By default this script validates readiness and prints the exact submit command.
It only performs the submission when --yes is supplied.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


FATAL_MARKERS = (
    "Traceback",
    "RuntimeError",
    "FileNotFoundError",
    "KeyError",
    "CUDA out of memory",
    "Killed",
    "Notebook Timeout",
    "row/column mismatch",
)


def kaggle_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    commands = [["kaggle", *args], [sys.executable, "-m", "kaggle.cli", *args]]
    failures: list[subprocess.CompletedProcess[str]] = []
    for command in commands:
        try:
            result = subprocess.run(
                command,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                env=env,
            )
        except FileNotFoundError:
            failures.append(subprocess.CompletedProcess(command, 127, "", f"not found: {command[0]}"))
            continue
        if result.returncode == 0:
            return result
        failures.append(result)
    for failure in failures:
        if failure.stdout or failure.stderr:
            return failure
    return failures[-1]


def safe_slug(value: str) -> str:
    return value.replace("/", "__").replace("\\", "__").replace(" ", "_")


def default_out_dir(competition: str, kernel: str, version: str | None) -> Path:
    suffix = f"-v{version}" if version else ""
    return Path("research") / competition / "submission_checks" / f"{safe_slug(kernel)}{suffix}"


def check_status(kernel: str) -> None:
    result = kaggle_cmd("kernels", "status", kernel)
    status = result.stdout.strip() or result.stderr.strip()
    print(f"## kernel status: {status}")
    if result.returncode != 0:
        raise SystemExit(status or "failed to query kernel status")
    if "KernelWorkerStatus.COMPLETE" not in result.stdout:
        raise SystemExit("refusing to submit: kernel is not COMPLETE")


def pull_output(kernel: str, out_dir: Path, version: str | None) -> Path | None:
    out_dir.mkdir(parents=True, exist_ok=True)
    args = ["kernels", "output", kernel, "-p", str(out_dir)]
    if version:
        args.extend(["--version", version])
    result = kaggle_cmd(*args)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        raise SystemExit("failed to pull kernel output")
    return next(out_dir.glob("*.log"), None)


def scan_log(log_path: Path | None) -> None:
    if log_path is None:
        print("[WARN] no .log file found in pulled output")
        return
    text = log_path.read_text(encoding="utf-8", errors="replace")
    hits = [marker for marker in FATAL_MARKERS if marker in text]
    if hits:
        print(f"[ERROR] fatal log markers found: {', '.join(hits)}")
        raise SystemExit("refusing to submit: log verification failed")
    print("## log verification: OK")


def ensure_output_file(out_dir: Path, filename: str) -> None:
    path = out_dir / filename
    if not path.exists():
        raise SystemExit(f"refusing to submit: output file not found after pull: {path}")
    print(f"## output file present: {path}")


def submit(args: argparse.Namespace) -> int:
    version = args.version
    out_dir = args.out_dir or default_out_dir(args.competition, args.kernel, version)

    if not args.skip_status:
        check_status(args.kernel)
    if not args.skip_output_check:
        log_path = pull_output(args.kernel, out_dir, version)
        scan_log(log_path)
        ensure_output_file(out_dir, args.file)

    submit_args = [
        "competitions",
        "submit",
        args.competition,
        "-k",
        args.kernel,
        "-f",
        args.file,
        "-m",
        args.message,
    ]
    if version:
        submit_args.extend(["-v", version])

    printable = "kaggle " + " ".join(f'"{x}"' if " " in x else x for x in submit_args)
    print("## submit command")
    print(printable)

    if not args.yes:
        print("## verdict: READY")
        print("refusing to submit without --yes; ask the user before consuming quota")
        return 0

    result = kaggle_cmd(*submit_args)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    print("## submitted")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition", help="Competition slug")
    parser.add_argument("--kernel", required=True, help="<owner>/<notebook-slug>")
    parser.add_argument("--version", help="Notebook version to submit, e.g. 3 or 'Version 3'")
    parser.add_argument("--file", default="submission.csv", help="Output filename produced by the notebook")
    parser.add_argument("-m", "--message", required=True, help="Submission message")
    parser.add_argument("--out-dir", type=Path, help="Directory used to pull output for validation")
    parser.add_argument("--skip-status", action="store_true", help="Do not require latest kernel status to be COMPLETE")
    parser.add_argument("--skip-output-check", action="store_true", help="Do not pull output/log before submit")
    parser.add_argument("--yes", action="store_true", help="Actually submit after validation")
    args = parser.parse_args()
    return submit(args)


if __name__ == "__main__":
    sys.exit(main())
