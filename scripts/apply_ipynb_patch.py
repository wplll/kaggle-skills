"""Apply idempotent source replacements to Jupyter notebook cells."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


def cell_source(cell: dict[str, Any]) -> str:
    source = cell.get("source", "")
    return "".join(source) if isinstance(source, list) else str(source)


def set_cell_source(cell: dict[str, Any], source: str) -> None:
    cell["source"] = source.splitlines(keepends=True)


def load_patches(path: Path | None, inline: list[str]) -> list[dict[str, Any]]:
    patches: list[dict[str, Any]] = []
    if path:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit("patch file must be a JSON list")
        patches.extend(data)

    for item in inline:
        parts = item.split("::", 2)
        if len(parts) != 3:
            raise SystemExit("--patch must look like CELL::BEFORE::AFTER")
        patches.append({"cell": int(parts[0]), "before": parts[1], "after": parts[2]})

    if not patches:
        raise SystemExit("provide --patch-file or --patch")
    return patches


def apply_patches(nb_path: Path, patches: list[dict[str, Any]]) -> int:
    notebook = json.loads(nb_path.read_text(encoding="utf-8"))
    cells = notebook.get("cells")
    if not isinstance(cells, list):
        raise SystemExit("notebook JSON has no cells list")

    applied = 0
    already = 0
    for patch in patches:
        cell_idx = int(patch["cell"])
        before = str(patch["before"])
        after = str(patch["after"])
        try:
            cell = cells[cell_idx]
        except IndexError as exc:
            raise SystemExit(f"cell index out of range: {cell_idx}") from exc

        source = cell_source(cell)
        if before in source:
            source = source.replace(before, after, 1)
            set_cell_source(cell, source)
            applied += 1
            print(f"[APPLIED] cell {cell_idx}: {before!r} -> {after!r}")
        elif after in source:
            already += 1
            print(f"[ALREADY] cell {cell_idx}: {after!r}")
        else:
            raise SystemExit(
                f"[ERROR] cell {cell_idx}: anchor not found; neither before nor after exists\n"
                f"before={before!r}\nafter={after!r}"
            )

    nb_path.write_text(json.dumps(notebook, indent=1, ensure_ascii=False), encoding="utf-8")
    print(f"applied={applied} already={already} total={applied + already}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("notebook", type=Path)
    parser.add_argument("--patch-file", type=Path, help="JSON list of {cell,before,after}")
    parser.add_argument("--patch", action="append", default=[], help="Inline patch: CELL::BEFORE::AFTER")
    args = parser.parse_args()
    patches = load_patches(args.patch_file, args.patch)
    return apply_patches(args.notebook, patches)


if __name__ == "__main__":
    sys.exit(main())

