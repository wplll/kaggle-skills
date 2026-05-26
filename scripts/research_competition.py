"""Create a read-only Kaggle competition research report."""
from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen


KERNEL_SORTS = ["voteCount", "scoreDescending", "commentCount", "dateRun"]
TOPIC_SORTS = ["hot", "top", "new", "active"]


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def run_kaggle(args: list[str], offline: bool) -> dict[str, object]:
    if offline:
        return {"args": args, "returncode": None, "stdout": "", "stderr": "offline mode"}
    env = {**os.environ, "PYTHONUTF8": "1", "PYTHONIOENCODING": "utf-8"}
    commands = [["kaggle", *args], [sys.executable, "-m", "kaggle.cli", *args]]
    failures: list[dict[str, object]] = []
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
            failures.append({"args": args, "returncode": 127, "stdout": "", "stderr": f"not found: {command[0]}"})
            continue
        current = {"args": args, "returncode": result.returncode, "stdout": result.stdout, "stderr": result.stderr}
        if result.returncode == 0:
            return current
        failures.append(current)
    for failure in failures:
        if failure.get("stdout") or failure.get("stderr"):
            return failure
    return failures[-1] if failures else {"args": args, "returncode": 1, "stdout": "", "stderr": "unknown failure"}


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    try:
        return list(csv.DictReader(text.splitlines()))
    except csv.Error:
        return []


def collect_kernels(comp: str, out_dir: Path, page_size: int, offline: bool) -> list[dict[str, object]]:
    collected: list[dict[str, object]] = []
    for sort in KERNEL_SORTS:
        command = ["kernels", "list", "--competition", comp, "--sort-by", sort, "--page-size", str(page_size), "-v"]
        result = run_kaggle(command, offline)
        write_text(out_dir / "raw" / f"kernels_{sort}.txt", str(result["stdout"]) + str(result["stderr"]))
        rows = parse_csv_rows(str(result["stdout"]))
        collected.append({"sort": sort, "command": command, "returncode": result["returncode"], "rows": rows})
    return collected


def collect_topics(comp: str, out_dir: Path, page_size: int, offline: bool) -> list[dict[str, object]]:
    collected: list[dict[str, object]] = []
    for sort in TOPIC_SORTS:
        command = ["competitions", "topics", "list", comp, "--sort-by", sort, "--page-size", str(page_size), "-v"]
        result = run_kaggle(command, offline)
        if result["returncode"] not in (0, None):
            command = ["competitions", "topics", comp, "--sort-by", sort, "--page-size", str(page_size), "-v"]
            result = run_kaggle(command, offline)
        write_text(out_dir / "raw" / f"topics_{sort}.txt", str(result["stdout"]) + str(result["stderr"]))
        rows = parse_csv_rows(str(result["stdout"]))
        collected.append({"sort": sort, "command": command, "returncode": result["returncode"], "rows": rows})
    return collected


def fetch_json(url: str, offline: bool) -> dict[str, object]:
    if offline:
        return {}
    request = Request(url, headers={"User-Agent": "kaggle-skill/0.1"})
    last_error: Exception | None = None
    for attempt in range(3):
        try:
            with urlopen(request, timeout=30) as response:
                return json.loads(response.read().decode("utf-8", errors="replace"))
        except Exception as exc:
            last_error = exc
            time.sleep(1 + attempt)
    raise RuntimeError(f"failed to fetch {url}: {last_error}")


def topic_signal_score(topic: dict[str, object]) -> int:
    title = str(topic.get("title", "")).lower()
    score = 0
    for keyword in ("submit", "submission", "metric", "lb", "cv", "leak", "external", "pseudo", "score", "timeout", "audio", "rule"):
        if keyword in title:
            score += 10
    if str(topic.get("authorType", "")).upper() == "HOST":
        score += 50
    try:
        score += int(topic.get("votes") or 0)
    except (TypeError, ValueError):
        pass
    return score


def topic_summary(detail: dict[str, object]) -> dict[str, object]:
    topic = detail.get("forumTopic") if isinstance(detail.get("forumTopic"), dict) else detail
    first_message = topic.get("firstMessage", {}) if isinstance(topic, dict) else {}
    raw = str(first_message.get("rawMarkdown", ""))
    comments = detail.get("comments") or topic.get("comments") or []
    return {
        "id": topic.get("id") if isinstance(topic, dict) else None,
        "title": topic.get("name") or topic.get("title") if isinstance(topic, dict) else None,
        "author": topic.get("authorUserDisplayName") if isinstance(topic, dict) else None,
        "url": "https://www.kaggle.com" + str(topic.get("url", "")) if isinstance(topic, dict) else "",
        "comment_count": len(comments) if isinstance(comments, list) else None,
        "snippet": " ".join(raw.split())[:700],
    }


def collect_discussions_api(comp: str, out_dir: Path, page_size: int, topic_detail_count: int, offline: bool) -> dict[str, object]:
    if offline:
        return {"competition": {}, "forum_id": None, "topics": [], "topic_details": [], "error": "offline mode"}
    try:
        comp_url = f"https://www.kaggle.com/api/i/competitions.CompetitionService/GetCompetition?competitionName={comp}"
        competition = fetch_json(comp_url, offline)
        write_text(out_dir / "raw" / "discussion_competition.json", json.dumps(competition, indent=2, ensure_ascii=False))
        forum_id = competition.get("forumId")
        if not forum_id:
            return {"competition": competition, "forum_id": None, "topics": [], "topic_details": [], "error": "forumId missing"}
        topic_url = (
            "https://www.kaggle.com/api/i/discussions.DiscussionsService/GetTopicListByForumId"
            f"?forumId={forum_id}&page=1"
        )
        topic_payload = fetch_json(topic_url, offline)
        write_text(out_dir / "raw" / "discussion_topics_page1.json", json.dumps(topic_payload, indent=2, ensure_ascii=False))
        topics = topic_payload.get("topics", [])
        if isinstance(topics, list):
            topics = topics[:page_size]
        else:
            topics = []
        detail_dir = out_dir / "raw" / "topic_details"
        detail_dir.mkdir(parents=True, exist_ok=True)
        topic_details: list[dict[str, object]] = []
        selected_topics = sorted(topics, key=topic_signal_score, reverse=True)[:topic_detail_count]
        for topic in selected_topics:
            topic_id = topic.get("id") if isinstance(topic, dict) else None
            if topic_id is None:
                continue
            detail_url = (
                "https://www.kaggle.com/api/i/discussions.DiscussionsService/GetForumTopicById"
                f"?forumTopicId={topic_id}&includeComments=true"
            )
            try:
                detail = fetch_json(detail_url, offline)
            except Exception as exc:
                topic_details.append({"id": topic_id, "error": str(exc)})
                continue
            write_text(detail_dir / f"{topic_id}.json", json.dumps(detail, indent=2, ensure_ascii=False))
            topic_details.append(topic_summary(detail))
        return {"competition": competition, "forum_id": forum_id, "topics": topics, "topic_details": topic_details, "error": None}
    except Exception as exc:
        return {"competition": {}, "forum_id": None, "topics": [], "topic_details": [], "error": str(exc)}


def collect_competition(comp: str, out_dir: Path, offline: bool) -> dict[str, object]:
    commands = {
        "search": ["competitions", "list", "-s", comp, "-v"],
        "files": ["competitions", "files", comp, "-v"],
    }
    results: dict[str, object] = {}
    for name, command in commands.items():
        result = run_kaggle(command, offline)
        write_text(out_dir / "raw" / f"competition_{name}.txt", str(result["stdout"]) + str(result["stderr"]))
        results[name] = result
    return results


def unique_kernel_refs(kernel_batches: list[dict[str, object]]) -> list[str]:
    refs: list[str] = []
    seen: set[str] = set()
    for batch in kernel_batches:
        for row in batch.get("rows", []):
            if not isinstance(row, dict):
                continue
            ref = row.get("ref") or row.get("kernelRef") or row.get("url")
            if ref and ref not in seen:
                seen.add(ref)
                refs.append(ref)
    return refs


def unique_topic_ids(topic_batches: list[dict[str, object]]) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for batch in topic_batches:
        for row in batch.get("rows", []):
            if not isinstance(row, dict):
                continue
            topic_id = row.get("id") or row.get("topicId")
            if topic_id and topic_id not in seen:
                seen.add(topic_id)
                ids.append(topic_id)
    return ids


def topic_ids_from_api(api_data: dict[str, object]) -> list[str]:
    ids: list[str] = []
    for topic in api_data.get("topics", []) or []:
        if isinstance(topic, dict) and topic.get("id") is not None:
            ids.append(str(topic["id"]))
    return ids


def table_from_batches(batches: list[dict[str, object]], max_rows: int = 20) -> str:
    lines = ["| sort | item | fields |", "|---|---|---|"]
    count = 0
    for batch in batches:
        sort = str(batch["sort"])
        rows = batch.get("rows", [])
        if not rows:
            lines.append(f"| {sort} | no parsed rows | returncode={batch.get('returncode')} |")
            continue
        for row in rows:
            if count >= max_rows:
                return "\n".join(lines)
            if not isinstance(row, dict):
                continue
            item = row.get("ref") or row.get("id") or row.get("title") or row.get("kernelRef") or "unknown"
            compact = "; ".join(f"{k}={v}" for k, v in list(row.items())[:8])
            lines.append(f"| {sort} | {item} | {compact} |")
            count += 1
    return "\n".join(lines)


def table_from_api_topics(api_data: dict[str, object], max_rows: int = 20) -> str:
    topics = api_data.get("topics", []) or []
    if not topics:
        return f"No API topics parsed. Error: {api_data.get('error')}"
    lines = ["| topic | author | votes | last activity | url |", "|---|---|---:|---|---|"]
    for topic in topics[:max_rows]:
        if not isinstance(topic, dict):
            continue
        author = topic.get("authorUser", {}) if isinstance(topic.get("authorUser"), dict) else {}
        title = str(topic.get("title", "")).replace("|", "\\|")
        url = "https://www.kaggle.com" + str(topic.get("topicUrl", ""))
        lines.append(
            f"| {title} | {author.get('displayName', '')} | {topic.get('votes', '')} | "
            f"{topic.get('lastCommentPostDate', topic.get('postDate', ''))} | {url} |"
        )
    return "\n".join(lines)


def competition_fact_table(api_data: dict[str, object]) -> str:
    comp = api_data.get("competition", {})
    if not isinstance(comp, dict) or not comp:
        return "Competition facts unavailable from API fallback."
    fields = [
        ("title", comp.get("title")),
        ("briefDescription", comp.get("briefDescription")),
        ("deadline", comp.get("deadline")),
        ("onlyAllowKernelSubmissions", comp.get("onlyAllowKernelSubmissions")),
        ("maxCpuRuntimeMinutes", comp.get("maxCpuRuntimeMinutes")),
        ("maxGpuRuntimeMinutes", comp.get("maxGpuRuntimeMinutes")),
        ("maxDailySubmissions", comp.get("maxDailySubmissions")),
        ("numScoredSubmissions", comp.get("numScoredSubmissions")),
        ("requiredSubmissionFilename", comp.get("requiredSubmissionFilename")),
        ("rowIdColumnName", comp.get("rowIdColumnName")),
        ("metric", (comp.get("evaluationAlgorithm") or {}).get("name") if isinstance(comp.get("evaluationAlgorithm"), dict) else None),
        ("forumId", comp.get("forumId")),
        ("rulesRequired", comp.get("rulesRequired")),
        ("license", (comp.get("license") or {}).get("name") if isinstance(comp.get("license"), dict) else None),
    ]
    lines = ["| field | value |", "|---|---|"]
    for name, value in fields:
        lines.append(f"| {name} | {value} |")
    return "\n".join(lines)


def topic_detail_table(api_data: dict[str, object]) -> str:
    details = api_data.get("topic_details", []) or []
    if not details:
        return "No topic details archived."
    lines = ["| topic | author | comments | signal |", "|---|---|---:|---|"]
    for detail in details:
        if not isinstance(detail, dict):
            continue
        title = str(detail.get("title", detail.get("id", ""))).replace("|", "\\|")
        snippet = str(detail.get("snippet", detail.get("error", ""))).replace("|", "\\|")
        lines.append(f"| {title} | {detail.get('author', '')} | {detail.get('comment_count', '')} | {snippet[:240]} |")
    return "\n".join(lines)


def write_report(
    comp: str,
    out_dir: Path,
    competition: dict[str, object],
    kernels: list[dict[str, object]],
    topics: list[dict[str, object]],
    discussion_api: dict[str, object],
    offline: bool,
) -> None:
    timestamp = now_iso()
    report = f"""# Kaggle Research Report: {comp}

Generated at: {timestamp}

Mode: {"offline skeleton" if offline else "Kaggle CLI collection"}

## Competition Overview

Raw metadata is archived in `raw/competition_search.txt` and `raw/competition_files.txt`.

{competition_fact_table(discussion_api)}

Manual checks still required:

- Rules page and external data policy
- Runtime, accelerator, internet, and Kernel-only constraints
- Whether competition rules have been accepted by the current account

## Public Code Candidates

{table_from_batches(kernels)}

## Discussion Signals

### API Topics

Forum ID: {discussion_api.get("forum_id")}

{table_from_api_topics(discussion_api)}

### Archived Topic Details

{topic_detail_table(discussion_api)}

### CLI Topics

{table_from_batches(topics)}

## Baseline Recommendation

Pending agent synthesis. Prefer a candidate that is reproducible, has accessible dependencies, writes a valid submission, fits sandbox limits, and has clear community validation.

## Optimization Opportunities

- Phase 0: replay selected baseline.
- Phase 1: apply one low-risk improvement after baseline verification.
- Later phases: one variable per leaderboard submission.

## Risks And Blockers

- Do not consume LB quota without user confirmation.
- Verify all dataset, kernel, and model sources before push.
- Treat Discussion claims about leaks or external data as compliance-sensitive until confirmed.
- Dry-run success does not prove hidden-test runtime safety.

## Source Archive

- `raw/kernels_*.txt`
- `raw/topics_*.txt`
- `state.json`
"""
    write_text(out_dir / "report.md", report)

    state = {
        "competition": comp,
        "last_checked_at": timestamp,
        "offline": offline,
        "seen_kernel_refs": unique_kernel_refs(kernels),
        "seen_topic_ids": sorted(set(unique_topic_ids(topics) + topic_ids_from_api(discussion_api))),
        "seen_comment_ids": [],
        "selected_baseline": None,
        "experiment_history": [],
        "known_blockers": [],
        "watch_keywords": ["baseline", "LB", "CV", "metric", "leak", "rule", "external data", "submission", "timeout", "OOM"],
    }
    write_text(out_dir / "state.json", json.dumps(state, indent=2, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("competition", help="Kaggle competition slug")
    parser.add_argument("--root", type=Path, default=Path("research"), help="Research output root")
    parser.add_argument("--page-size", type=int, default=20)
    parser.add_argument("--topic-details", type=int, default=5, help="Number of high-signal Discussion topics to archive")
    parser.add_argument("--offline", action="store_true", help="Create report skeleton without running Kaggle CLI")
    args = parser.parse_args()

    out_dir = args.root / args.competition
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "raw").mkdir(exist_ok=True)

    competition = collect_competition(args.competition, out_dir, args.offline)
    kernels = collect_kernels(args.competition, out_dir, args.page_size, args.offline)
    topics = collect_topics(args.competition, out_dir, args.page_size, args.offline)
    discussion_api = collect_discussions_api(args.competition, out_dir, args.page_size, args.topic_details, args.offline)
    write_report(args.competition, out_dir, competition, kernels, topics, discussion_api, args.offline)
    print(f"wrote {out_dir / 'report.md'}")
    print(f"wrote {out_dir / 'state.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
