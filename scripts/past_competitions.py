"""Archive past editions and similar competitions for a Kaggle base competition.

Inputs (any combination):
  --past <slug>          explicit competition slug (repeatable)
  --auto-years            auto-detect <base>-YYYY style siblings
  --years YYYY YYYY       year range for auto detection (inclusive)
  --search <keyword>      Kaggle competition keyword search (repeatable)
  --include-current       include the base slug itself in the archive

For each discovered competition the script archives:
  - competition metadata via the internal JSON API (forumId, runtime caps, metric, ...)
  - top public kernels sorted by voteCount and scoreDescending
  - discussion topics, with high-signal "solution / writeup / Nth place" threads expanded

Output layout under <root>/<base>/past/:
  index.md            overview of all archived competitions
  past_state.json     resolved slugs and archive timestamps
  <slug>/
    summary.md        per-competition write-up
    raw/
      competition.json
      kernels_<sort>.txt
      topics.json
      topic_<id>.json
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote
from urllib.request import Request, urlopen


KERNEL_SORTS = ("voteCount", "scoreDescending")
TOPIC_SOLUTION_KEYWORDS = (
    "1st place",
    "2nd place",
    "3rd place",
    "place solution",
    "place writeup",
    "place write-up",
    "winning solution",
    "gold solution",
    "silver solution",
    "winners solution",
    "winner solution",
    "our solution",
    "my solution",
    "solution writeup",
    "solution summary",
    "competition write-up",
    "competition writeup",
    "approach summary",
    "final solution",
    "team solution",
)
TOPIC_HOTSPOT_KEYWORDS = (
    "leak",
    "external data",
    "rule",
    "metric",
    "cv",
    "lb",
    "shake",
    "trick",
    "post-process",
    "postprocess",
    "ensemble",
    "pseudo",
    "label",
)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


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


def parse_csv_rows(text: str) -> list[dict[str, str]]:
    if not text.strip():
        return []
    try:
        return list(csv.DictReader(text.splitlines()))
    except csv.Error:
        return []


def detect_base_and_year(slug: str) -> tuple[str, int | None]:
    match = re.match(r"^(.+?)[-_](\d{4})$", slug)
    if not match:
        return slug, None
    return match.group(1), int(match.group(2))


def candidate_year_slugs(base: str, slug_template: str, years: tuple[int, int]) -> list[str]:
    low, high = sorted(years)
    return [slug_template.format(base=base, year=year) for year in range(low, high + 1)]


def verify_slug(slug: str, offline: bool) -> bool:
    if offline:
        return True
    result = run_kaggle(["competitions", "list", "-s", slug, "-v"], offline)
    rows = parse_csv_rows(str(result.get("stdout", "")))
    target = slug.lower()
    for row in rows:
        ref = str(row.get("ref") or row.get("url") or row.get("Ref") or "").lower()
        if ref.endswith("/" + target) or ref == target:
            return True
    return False


def search_competitions(keyword: str, offline: bool) -> list[str]:
    result = run_kaggle(["competitions", "list", "-s", keyword, "-v"], offline)
    rows = parse_csv_rows(str(result.get("stdout", "")))
    slugs: list[str] = []
    seen: set[str] = set()
    for row in rows:
        ref = str(row.get("ref") or row.get("url") or row.get("Ref") or "")
        if not ref:
            continue
        slug = ref.rstrip("/").rsplit("/", 1)[-1]
        if slug and slug not in seen:
            seen.add(slug)
            slugs.append(slug)
    return slugs


def collect_competition(slug: str, raw_dir: Path, offline: bool) -> dict[str, object]:
    if offline:
        return {}
    url = f"https://www.kaggle.com/api/i/competitions.CompetitionService/GetCompetition?competitionName={quote(slug)}"
    try:
        data = fetch_json(url, offline)
    except Exception as exc:
        return {"error": str(exc)}
    write_text(raw_dir / "competition.json", json.dumps(data, indent=2, ensure_ascii=False))
    return data


def collect_kernels(slug: str, raw_dir: Path, page_size: int, offline: bool) -> dict[str, list[dict[str, str]]]:
    out: dict[str, list[dict[str, str]]] = {}
    for sort in KERNEL_SORTS:
        result = run_kaggle(
            ["kernels", "list", "--competition", slug, "--sort-by", sort, "--page-size", str(page_size), "-v"],
            offline,
        )
        write_text(raw_dir / f"kernels_{sort}.txt", str(result.get("stdout", "")) + str(result.get("stderr", "")))
        out[sort] = parse_csv_rows(str(result.get("stdout", "")))
    return out


def topic_signal_score(topic: dict[str, object]) -> int:
    title = str(topic.get("title", "")).lower()
    score = 0
    for keyword in TOPIC_SOLUTION_KEYWORDS:
        if keyword in title:
            score += 100
    for keyword in TOPIC_HOTSPOT_KEYWORDS:
        if keyword in title:
            score += 15
    if str(topic.get("authorType", "")).upper() == "HOST":
        score += 30
    try:
        score += int(topic.get("votes") or 0)
    except (TypeError, ValueError):
        pass
    return score


def topic_summary(detail: dict[str, object]) -> dict[str, object]:
    topic = detail.get("forumTopic") if isinstance(detail.get("forumTopic"), dict) else detail
    if not isinstance(topic, dict):
        topic = {}
    first_message = topic.get("firstMessage", {}) if isinstance(topic.get("firstMessage"), dict) else {}
    raw = str(first_message.get("rawMarkdown", ""))
    comments = detail.get("comments") or topic.get("comments") or []
    return {
        "id": topic.get("id"),
        "title": topic.get("name") or topic.get("title"),
        "author": topic.get("authorUserDisplayName"),
        "url": "https://www.kaggle.com" + str(topic.get("url", "")) if topic.get("url") else "",
        "comment_count": len(comments) if isinstance(comments, list) else None,
        "snippet": " ".join(raw.split())[:600],
    }


def collect_topics(competition_data: dict[str, object], raw_dir: Path, page_size: int, detail_count: int, offline: bool) -> dict[str, object]:
    if offline:
        return {"forum_id": None, "topics": [], "topic_details": [], "error": "offline"}
    forum_id = competition_data.get("forumId") if isinstance(competition_data, dict) else None
    if not forum_id:
        return {"forum_id": None, "topics": [], "topic_details": [], "error": "forumId missing"}

    base_url = "https://www.kaggle.com/api/i/discussions.DiscussionsService/GetTopicListByForumId"
    pages: list[dict[str, object]] = []
    aggregated: list[dict[str, object]] = []
    seen_ids: set[object] = set()
    for page in range(1, 4):
        try:
            payload = fetch_json(f"{base_url}?forumId={forum_id}&page={page}", offline)
        except Exception as exc:
            pages.append({"page": page, "error": str(exc)})
            break
        pages.append({"page": page, "payload": payload})
        topics = payload.get("topics", []) if isinstance(payload, dict) else []
        if not isinstance(topics, list) or not topics:
            break
        for topic in topics:
            if not isinstance(topic, dict):
                continue
            topic_id = topic.get("id")
            if topic_id is None or topic_id in seen_ids:
                continue
            seen_ids.add(topic_id)
            aggregated.append(topic)
        if len(aggregated) >= page_size * 3:
            break
    write_text(raw_dir / "topics.json", json.dumps(pages, indent=2, ensure_ascii=False))

    selected = sorted(aggregated, key=topic_signal_score, reverse=True)[:detail_count]
    detail_dir = raw_dir / "topic_details"
    topic_details: list[dict[str, object]] = []
    for topic in selected:
        topic_id = topic.get("id")
        if topic_id is None:
            continue
        detail_url = (
            "https://www.kaggle.com/api/i/discussions.DiscussionsService/GetForumTopicById"
            f"?forumTopicId={topic_id}&includeComments=true"
        )
        try:
            detail = fetch_json(detail_url, offline)
        except Exception as exc:
            topic_details.append({"id": topic_id, "title": topic.get("title"), "error": str(exc)})
            continue
        write_text(detail_dir / f"{topic_id}.json", json.dumps(detail, indent=2, ensure_ascii=False))
        summary = topic_summary(detail)
        summary["signal"] = topic_signal_score(topic)
        topic_details.append(summary)

    return {
        "forum_id": forum_id,
        "topics": aggregated[: page_size * 3],
        "topic_details": topic_details,
        "error": None,
    }


def kernel_table(kernels: dict[str, list[dict[str, str]]], max_rows: int = 12) -> str:
    if not any(kernels.values()):
        return "_no public kernels parsed_"
    lines = ["| sort | ref | title | votes | score | author |", "|---|---|---|---:|---:|---|"]
    count = 0
    for sort, rows in kernels.items():
        if not rows:
            lines.append(f"| {sort} | (empty) | | | | |")
            continue
        for row in rows:
            if count >= max_rows * len(KERNEL_SORTS):
                break
            ref = str(row.get("ref", "")).replace("|", "\\|")
            title = str(row.get("title", "")).replace("|", "\\|")
            votes = row.get("totalVotes", row.get("votes", ""))
            score = row.get("publicScore", row.get("score", ""))
            author = row.get("author", "")
            lines.append(f"| {sort} | {ref} | {title} | {votes} | {score} | {author} |")
            count += 1
    return "\n".join(lines)


def topic_solution_table(topic_details: list[dict[str, object]]) -> str:
    if not topic_details:
        return "_no archived solution / hotspot threads_"
    lines = ["| signal | title | author | comments | snippet |", "|---:|---|---|---:|---|"]
    for detail in sorted(topic_details, key=lambda item: item.get("signal", 0), reverse=True):
        title = str(detail.get("title", "")).replace("|", "\\|")
        snippet = str(detail.get("snippet", "")).replace("|", "\\|")[:240]
        lines.append(
            f"| {detail.get('signal', '')} | {title} | {detail.get('author', '')} "
            f"| {detail.get('comment_count', '')} | {snippet} |"
        )
    return "\n".join(lines)


def render_competition_summary(slug: str, competition: dict[str, object], kernels: dict[str, list[dict[str, str]]], topics: dict[str, object]) -> str:
    facts = []
    if isinstance(competition, dict) and competition:
        for field in (
            "title",
            "deadline",
            "onlyAllowKernelSubmissions",
            "maxCpuRuntimeMinutes",
            "maxGpuRuntimeMinutes",
            "maxDailySubmissions",
            "requiredSubmissionFilename",
            "rowIdColumnName",
            "forumId",
        ):
            value = competition.get(field)
            if value is not None:
                facts.append(f"- {field}: {value}")
        evaluation = competition.get("evaluationAlgorithm")
        if isinstance(evaluation, dict) and evaluation.get("name"):
            facts.append(f"- metric: {evaluation['name']}")
    fact_block = "\n".join(facts) if facts else "_no API metadata_"

    return (
        f"# Past Edition Archive: {slug}\n"
        f"\nGenerated at: {now_iso()}\n"
        f"\nKaggle URL: https://www.kaggle.com/competitions/{slug}\n"
        f"\n## Competition Facts\n\n{fact_block}\n"
        f"\n## Top Public Kernels\n\n{kernel_table(kernels)}\n"
        f"\n## Solution / Hotspot Threads\n\n"
        f"Forum ID: {topics.get('forum_id')}\n\n"
        f"{topic_solution_table(topics.get('topic_details') or [])}\n"
        f"\n## Source Archive\n\n- raw/competition.json\n- raw/kernels_*.txt\n- raw/topics.json\n- raw/topic_details/<id>.json\n"
    )


def render_index(base_slug: str, archived: list[dict[str, object]]) -> str:
    if not archived:
        return f"# Past Editions Index: {base_slug}\n\nNo competitions archived.\n"
    lines = [
        f"# Past Editions Index: {base_slug}",
        "",
        f"Generated at: {now_iso()}",
        "",
        "## Archived Competitions",
        "",
        "| slug | source | metric | deadline | top kernel | top solution thread |",
        "|---|---|---|---|---|---|",
    ]
    for entry in archived:
        comp = entry.get("competition", {}) if isinstance(entry.get("competition"), dict) else {}
        evaluation = comp.get("evaluationAlgorithm") if isinstance(comp, dict) else None
        metric = evaluation.get("name") if isinstance(evaluation, dict) else ""
        deadline = comp.get("deadline", "") if isinstance(comp, dict) else ""
        top_kernel = ""
        kernels = entry.get("kernels", {}) or {}
        for sort in KERNEL_SORTS:
            rows = kernels.get(sort) or []
            if rows:
                top_kernel = str(rows[0].get("ref", ""))
                break
        top_thread = ""
        topic_details = (entry.get("topics") or {}).get("topic_details") or []
        if topic_details:
            top = max(topic_details, key=lambda item: item.get("signal", 0))
            top_thread = str(top.get("title", "")).replace("|", "\\|")
        lines.append(
            f"| {entry['slug']} | {entry.get('source', '')} | {metric or ''} | {deadline} | {top_kernel} | {top_thread} |"
        )
    lines.extend([
        "",
        "## Notes",
        "",
        "- Solution / writeup threads are heuristically ranked; verify by reading raw topic JSON.",
        "- Top kernel column shows highest-vote kernel; cross-check `kernels_scoreDescending.txt` for leaderboard-facing candidates.",
        "- Past-edition rule and metric drift can invalidate transferred tricks. Re-read each competition's rules before reusing code.",
        "",
    ])
    return "\n".join(lines)


def resolve_candidates(args: argparse.Namespace) -> list[tuple[str, str]]:
    base, base_year = detect_base_and_year(args.competition)
    candidates: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(slug: str, source: str) -> None:
        slug = slug.strip().lower()
        if not slug or slug in seen:
            return
        if slug == args.competition.lower() and not args.include_current:
            return
        seen.add(slug)
        candidates.append((slug, source))

    for slug in args.past or []:
        add(slug, "explicit")

    if args.auto_years:
        if base_year is None and not args.years:
            print(f"[warn] cannot auto-detect year suffix from {args.competition!r}; skip auto-years", file=sys.stderr)
        else:
            if args.years:
                years = (int(args.years[0]), int(args.years[1]))
            else:
                years = (base_year - 5, base_year - 1) if base_year else (0, 0)
            template = "{base}-{year}"
            for slug in candidate_year_slugs(base, template, years):
                add(slug, "auto-year")

    for keyword in args.search or []:
        for slug in search_competitions(keyword, args.offline):
            add(slug, f"search:{keyword}")

    if args.include_current:
        add(args.competition, "current")

    return candidates


def archive_one(slug: str, source: str, base_dir: Path, page_size: int, topic_details: int, offline: bool) -> dict[str, object]:
    raw_dir = base_dir / slug / "raw"
    competition = collect_competition(slug, raw_dir, offline)
    kernels = collect_kernels(slug, raw_dir, page_size, offline)
    topics = collect_topics(competition if isinstance(competition, dict) else {}, raw_dir, page_size, topic_details, offline)
    summary = render_competition_summary(slug, competition if isinstance(competition, dict) else {}, kernels, topics)
    write_text(base_dir / slug / "summary.md", summary)
    return {
        "slug": slug,
        "source": source,
        "competition": competition,
        "kernels": kernels,
        "topics": topics,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("competition", help="Base Kaggle competition slug, e.g. birdclef-2026")
    parser.add_argument("--root", type=Path, default=Path("research"))
    parser.add_argument("--past", action="append", default=[], help="Explicit past competition slug (repeatable)")
    parser.add_argument("--auto-years", action="store_true", help="Try <base>-YYYY siblings inferred from the slug")
    parser.add_argument("--years", nargs=2, metavar=("LO", "HI"), help="Year range for --auto-years")
    parser.add_argument("--search", action="append", default=[], help="Kaggle keyword search (repeatable)")
    parser.add_argument("--include-current", action="store_true", help="Also archive the base slug itself")
    parser.add_argument("--page-size", type=int, default=15)
    parser.add_argument("--topic-details", type=int, default=8)
    parser.add_argument("--offline", action="store_true")
    parser.add_argument("--skip-verify", action="store_true", help="Skip Kaggle existence check before archiving")
    args = parser.parse_args()

    base_dir = args.root / args.competition / "past"
    base_dir.mkdir(parents=True, exist_ok=True)

    candidates = resolve_candidates(args)
    if not candidates:
        print("no past or similar competitions resolved; provide --past, --auto-years, or --search", file=sys.stderr)
        return 1

    archived: list[dict[str, object]] = []
    skipped: list[dict[str, str]] = []
    for slug, source in candidates:
        if not args.skip_verify and not verify_slug(slug, args.offline):
            print(f"[skip] {slug} (not visible to current account)")
            skipped.append({"slug": slug, "source": source, "reason": "not visible"})
            continue
        print(f"[archive] {slug} ({source})")
        try:
            archived.append(archive_one(slug, source, base_dir, args.page_size, args.topic_details, args.offline))
        except Exception as exc:
            print(f"[error] {slug}: {exc}")
            skipped.append({"slug": slug, "source": source, "reason": str(exc)})

    write_text(base_dir / "index.md", render_index(args.competition, archived))
    state = {
        "base": args.competition,
        "generated_at": now_iso(),
        "offline": args.offline,
        "archived": [{"slug": item["slug"], "source": item["source"]} for item in archived],
        "skipped": skipped,
    }
    write_text(base_dir / "past_state.json", json.dumps(state, indent=2, ensure_ascii=False))
    print(f"wrote {base_dir / 'index.md'}")
    print(f"wrote {base_dir / 'past_state.json'}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
