"""Install the current competition workflow skill without replacing existing files."""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys


SKILL_NAME = "ml-competition-workflow"
REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
SKILL_SOURCE = REPOSITORY_ROOT / "skills" / SKILL_NAME


def default_target_root() -> Path:
    codex_root = os.environ.get("CODEX_HOME")
    return (Path(codex_root).expanduser() if codex_root else Path.home() / ".codex") / "skills"


def read_payload(source: Path) -> dict[Path, bytes]:
    """Read only the skill payload; reject links and accidental non-document files."""
    if source.is_symlink() or not source.is_dir():
        raise ValueError(f"Skill source is missing or is a link: {source}")
    payload: dict[Path, bytes] = {}
    for item in sorted(source.rglob("*")):
        if item.is_symlink():
            raise ValueError(f"Skill payload contains a link: {item}")
        if item.is_dir():
            continue
        relative = item.relative_to(source)
        allowed = relative == Path("SKILL.md") or (
            relative.parts[0] in {"agents", "references"}
            and item.suffix in {".md", ".yaml"}
        )
        if not item.is_file() or not allowed:
            raise ValueError(f"Unexpected skill payload file: {relative}")
        payload[relative] = item.read_bytes()
    if Path("SKILL.md") not in payload:
        raise ValueError("The source skill has no SKILL.md")
    return payload


def install_skill(source: Path, target_root: Path) -> tuple[Path, bool]:
    payload = read_payload(source)
    destination = target_root.expanduser() / SKILL_NAME
    if destination.is_symlink():
        raise FileExistsError(f"Destination is a link; no changes made: {destination}")
    if destination.exists():
        if not destination.is_dir():
            raise FileExistsError(f"Destination is not a directory: {destination}")
        existing: dict[Path, bytes] = {}
        for item in destination.rglob("*"):
            if item.is_symlink():
                raise FileExistsError(f"Existing installation contains a link: {item}")
            if item.is_file():
                existing[item.relative_to(destination)] = item.read_bytes()
        if existing != payload:
            raise FileExistsError(
                f"Existing installation differs; preserved unchanged: {destination}. "
                "Choose another --target-root or explicitly manage your previous version."
            )
        return destination, False

    # Exclusive directory/file creation prevents a concurrent run from replacing data.
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.mkdir(exist_ok=False)
    for relative, content in payload.items():
        output = destination / relative
        output.parent.mkdir(parents=True, exist_ok=True)
        with output.open("xb") as handle:
            handle.write(content)
    return destination, True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target-root", type=Path, default=default_target_root(),
        help="Skill parent directory; defaults to CODEX_HOME/skills or ~/.codex/skills",
    )
    args = parser.parse_args()
    try:
        destination, created = install_skill(SKILL_SOURCE, args.target_root)
    except (OSError, ValueError) as exc:
        print(f"Installation stopped: {exc}", file=sys.stderr)
        print("No files were deleted. Any partial new installation is retained.", file=sys.stderr)
        return 2
    print(f"{'Installed' if created else 'Already identical'}: {destination}")
    print(f"Invoke with ${SKILL_NAME}; start a new session if discovery has not refreshed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
