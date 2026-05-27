"""Kaggle data download and dataset upload helper.

Subcommands:
  download-competition   Download official competition files
  download-dataset       Download a Kaggle Dataset
  init-upload            Write dataset-metadata.json for a local dataset
  preflight              Inspect local dataset metadata and files
  create                 Create a Kaggle Dataset (requires --yes)
  version                Create a new Kaggle Dataset version (requires --yes)
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import zipfile
from dataclasses import dataclass
from pathlib import Path


BLOCKED_NAMES = {
    ".git",
    ".hg",
    ".svn",
    "__pycache__",
    ".venv",
    "venv",
    "env",
    ".env",
    "kaggle.json",
}

SUSPICIOUS_SUFFIXES = {
    ".key",
    ".pem",
    ".pfx",
    ".p12",
    ".crt",
    ".sqlite",
    ".db",
    ".log",
}


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    command: list[str]


def kaggle_cmd(*args: str) -> CommandResult:
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    commands = [["kaggle", *args], [sys.executable, "-m", "kaggle.cli", *args]]
    failures: list[CommandResult] = []
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
            failures.append(CommandResult(127, "", f"not found: {command[0]}", command))
            continue
        current = CommandResult(result.returncode, result.stdout, result.stderr, command)
        if result.returncode == 0:
            return current
        failures.append(current)
    for failure in failures:
        if failure.stdout or failure.stderr:
            return failure
    return failures[-1]


def slugify(title: str) -> str:
    value = title.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def human_size(num: int) -> str:
    value = float(num)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}"
        value /= 1024
    return f"{value:.1f} GB"


def iter_files(root: Path) -> list[Path]:
    return [p for p in root.rglob("*") if p.is_file()]


def scan_local_dir(root: Path) -> tuple[list[Path], int, list[str]]:
    if not root.exists() or not root.is_dir():
        raise SystemExit(f"directory not found: {root}")
    files = iter_files(root)
    total = sum(p.stat().st_size for p in files)
    warnings: list[str] = []
    for path in files:
        parts = set(path.relative_to(root).parts)
        if parts & BLOCKED_NAMES:
            warnings.append(f"blocked/sensitive path: {path.relative_to(root)}")
        if path.suffix.lower() in SUSPICIOUS_SUFFIXES:
            warnings.append(f"suspicious suffix: {path.relative_to(root)}")
    if not files:
        warnings.append("directory contains no files")
    return files, total, warnings


def read_metadata(root: Path) -> dict[str, object] | None:
    path = root / "dataset-metadata.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def write_metadata(root: Path, dataset_id: str, title: str, licenses: list[dict[str, str]] | None = None) -> Path:
    if "/" not in dataset_id:
        raise SystemExit("--id must look like <owner>/<dataset-slug>")
    if slugify(title) != dataset_id.split("/", 1)[1]:
        print(f"[WARN] title slug {slugify(title)!r} does not match id suffix {dataset_id.split('/', 1)[1]!r}")
    metadata = {
        "id": dataset_id,
        "title": title,
        "licenses": licenses or [{"name": "CC0-1.0"}],
    }
    path = root / "dataset-metadata.json"
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False), encoding="utf-8")
    return path


def print_preflight(root: Path) -> int:
    files, total, warnings = scan_local_dir(root)
    metadata = read_metadata(root)
    print(f"directory: {root}")
    print(f"files: {len(files)}")
    print(f"size: {human_size(total)}")
    if metadata:
        print(f"metadata id: {metadata.get('id')}")
        print(f"metadata title: {metadata.get('title')}")
    else:
        warnings.append("dataset-metadata.json missing; run init-upload first")
    for warning in warnings:
        print(f"[WARN] {warning}")
    if any("blocked/sensitive" in w for w in warnings):
        print("## verdict: BLOCKED")
        return 1
    print("## verdict: PASS")
    return 0


def safe_extract(zip_path: Path, out_dir: Path, overwrite: bool) -> None:
    with zipfile.ZipFile(zip_path) as zf:
        conflicts: list[Path] = []
        for member in zf.infolist():
            if member.is_dir():
                continue
            target = out_dir / member.filename
            try:
                target.resolve().relative_to(out_dir.resolve())
            except ValueError as exc:
                raise SystemExit(f"unsafe zip path: {member.filename}") from exc
            if target.exists() and not overwrite:
                conflicts.append(target)
        if conflicts:
            preview = "\n".join(str(p) for p in conflicts[:10])
            raise SystemExit(f"extraction would overwrite files; use --overwrite if intended:\n{preview}")
        zf.extractall(out_dir)


def newest_zip(out_dir: Path) -> Path | None:
    zips = sorted(out_dir.glob("*.zip"), key=lambda p: p.stat().st_mtime, reverse=True)
    return zips[0] if zips else None


def download_competition(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    result = kaggle_cmd("competitions", "download", args.competition, "-p", str(out_dir))
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    if args.unzip:
        zip_path = newest_zip(out_dir)
        if zip_path is None:
            raise SystemExit(f"no zip downloaded into {out_dir}")
        safe_extract(zip_path, out_dir, args.overwrite)
        print(f"extracted: {zip_path}")
    return 0


def download_dataset(args: argparse.Namespace) -> int:
    out_dir = args.out_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    result = kaggle_cmd("datasets", "download", args.dataset, "-p", str(out_dir))
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        return result.returncode
    if args.unzip:
        zip_path = newest_zip(out_dir)
        if zip_path is None:
            raise SystemExit(f"no zip downloaded into {out_dir}")
        safe_extract(zip_path, out_dir, args.overwrite)
        print(f"extracted: {zip_path}")
    return 0


def init_upload(args: argparse.Namespace) -> int:
    args.dir.mkdir(parents=True, exist_ok=True)
    path = write_metadata(args.dir, args.id, args.title)
    print(f"wrote {path}")
    return print_preflight(args.dir)


def create_dataset(args: argparse.Namespace) -> int:
    verdict = print_preflight(args.dir)
    if verdict != 0:
        return verdict
    if not args.yes:
        raise SystemExit("refusing to upload without --yes")
    cmd = ["datasets", "create", "-p", str(args.dir)]
    if args.public:
        cmd.append("--public")
    result = kaggle_cmd(*cmd)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def version_dataset(args: argparse.Namespace) -> int:
    verdict = print_preflight(args.dir)
    if verdict != 0:
        return verdict
    if not args.yes:
        raise SystemExit("refusing to upload a new version without --yes")
    cmd = ["datasets", "version", "-p", str(args.dir), "-m", args.message]
    if args.public:
        print("[WARN] --public is ignored for version; dataset visibility is controlled by the existing dataset")
    result = kaggle_cmd(*cmd)
    print(result.stdout, end="")
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("download-competition", help="Download official competition files")
    p.add_argument("competition")
    p.add_argument("out_dir", type=Path)
    p.add_argument("--unzip", action="store_true")
    p.add_argument("--overwrite", action="store_true", help="Allow zip extraction to overwrite existing files")
    p.set_defaults(func=download_competition)

    p = sub.add_parser("download-dataset", help="Download a Kaggle Dataset")
    p.add_argument("dataset")
    p.add_argument("out_dir", type=Path)
    p.add_argument("--unzip", action="store_true")
    p.add_argument("--overwrite", action="store_true", help="Allow zip extraction to overwrite existing files")
    p.set_defaults(func=download_dataset)

    p = sub.add_parser("init-upload", help="Initialize dataset-metadata.json")
    p.add_argument("dir", type=Path)
    p.add_argument("--id", required=True, help="<owner>/<dataset-slug>")
    p.add_argument("--title", required=True)
    p.set_defaults(func=init_upload)

    p = sub.add_parser("preflight", help="Inspect local dataset directory")
    p.add_argument("dir", type=Path)
    p.set_defaults(func=lambda args: print_preflight(args.dir))

    p = sub.add_parser("create", help="Create a Kaggle Dataset")
    p.add_argument("dir", type=Path)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--public", action="store_true")
    p.set_defaults(func=create_dataset)

    p = sub.add_parser("version", help="Create a Kaggle Dataset version")
    p.add_argument("dir", type=Path)
    p.add_argument("-m", "--message", required=True)
    p.add_argument("--yes", action="store_true")
    p.add_argument("--public", action="store_true")
    p.set_defaults(func=version_dataset)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
