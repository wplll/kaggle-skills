"""Preflight checks for Kaggle kernel metadata."""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
from pathlib import Path


def slugify(title: str) -> str:
    value = title.lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


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


def strip_version(ref: str) -> str:
    return ref.split("/versions/", 1)[0]


def check_metadata(meta_path: Path, skip_network: bool = False) -> int:
    errors: list[str] = []
    warnings: list[str] = []

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"## verdict: BLOCKED\n- cannot read JSON: {exc}")
        return 1

    kernel_id = meta.get("id")
    title = meta.get("title")
    code_file = meta.get("code_file")

    if not kernel_id or "/" not in kernel_id:
        errors.append("id must exist and look like <user>/<slug>")
    if not title:
        errors.append("title must exist")
    if kernel_id and "/" in kernel_id and title:
        id_suffix = kernel_id.split("/", 1)[1]
        title_slug = slugify(title)
        if title_slug != id_suffix:
            errors.append(f"title slug {title_slug!r} != id suffix {id_suffix!r}")

    if not code_file:
        errors.append("code_file must exist in kernel-metadata.json")
    else:
        code_path = meta_path.parent / str(code_file)
        if not code_path.exists():
            errors.append(f"code_file not found: {code_path}")

    if meta.get("is_private") is not True:
        warnings.append("is_private should usually be true for experiment forks")

    if meta.get("enable_internet") is True:
        warnings.append("enable_internet=true; verify competition rules allow it")

    if skip_network:
        warnings.append("network checks skipped")
    else:
        for ds in meta.get("dataset_sources", []) or []:
            ds_ref = strip_version(str(ds))
            result = kaggle_cmd("datasets", "files", ds_ref)
            if result.returncode != 0:
                errors.append(f"dataset not attachable: {ds} ({result.stderr.strip() or result.stdout.strip()})")
            else:
                print(f"[OK] dataset source visible: {ds}")

        for comp in meta.get("competition_sources", []) or []:
            comp_ref = str(comp)
            result = kaggle_cmd("competitions", "list", "-s", comp_ref)
            if result.returncode != 0 or comp_ref not in result.stdout:
                errors.append(f"competition not found or not visible: {comp_ref}")
            else:
                print(f"[OK] competition visible: {comp_ref}")

        for src in meta.get("kernel_sources", []) or []:
            src_ref = strip_version(str(src))
            if "/" in src_ref:
                owner, slug = src_ref.split("/", 1)
                result = kaggle_cmd("kernels", "list", "--user", owner, "-s", slug)
            else:
                slug = src_ref
                result = kaggle_cmd("kernels", "list", "-s", slug)
            if result.returncode != 0 or slug.lower() not in result.stdout.lower():
                warnings.append(f"kernel source not confirmed visible: {src}")
            else:
                print(f"[OK] kernel source likely visible: {src}")

        for model in meta.get("model_sources", []) or []:
            warnings.append(f"model source requires manual workspace/access check: {model}")

    print("\n## preflight summary")
    for warning in warnings:
        print(f"[WARN] {warning}")
    if errors:
        print("## verdict: BLOCKED")
        for error in errors:
            print(f"[ERROR] {error}")
        return 1
    print("## verdict: PASS")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("metadata", type=Path, help="Path to kernel-metadata.json")
    parser.add_argument("--skip-network", action="store_true", help="Skip Kaggle visibility checks")
    args = parser.parse_args()
    return check_metadata(args.metadata, args.skip_network)


if __name__ == "__main__":
    sys.exit(main())
