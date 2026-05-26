"""Update a Kaggle research watch state without submitting anything."""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition", help="Kaggle competition slug")
    parser.add_argument("--root", type=Path, default=Path("research"))
    parser.add_argument("--offline", action="store_true")
    args = parser.parse_args()

    state_path = args.root / args.competition / "state.json"
    old_state = {}
    if state_path.exists():
        old_state = json.loads(state_path.read_text(encoding="utf-8"))

    script = Path(__file__).with_name("research_competition.py")
    command = [sys.executable, str(script), args.competition, "--root", str(args.root)]
    if args.offline:
        command.append("--offline")
    result = subprocess.run(command, text=True)
    if result.returncode != 0:
        return result.returncode

    new_state = json.loads(state_path.read_text(encoding="utf-8"))
    old_kernels = set(old_state.get("seen_kernel_refs", []))
    old_topics = set(old_state.get("seen_topic_ids", []))
    new_kernels = set(new_state.get("seen_kernel_refs", []))
    new_topics = set(new_state.get("seen_topic_ids", []))

    delta = {
        "new_kernel_refs": sorted(new_kernels - old_kernels),
        "new_topic_ids": sorted(new_topics - old_topics),
    }
    delta_path = args.root / args.competition / "watch_delta.json"
    delta_path.write_text(json.dumps(delta, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"wrote {delta_path}")
    if delta["new_kernel_refs"] or delta["new_topic_ids"]:
        print("new Kaggle content detected; update report synthesis before changing experiments")
    else:
        print("no new parsed kernels/topics detected")
    return 0


if __name__ == "__main__":
    sys.exit(main())

