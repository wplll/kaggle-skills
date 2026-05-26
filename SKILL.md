---
name: kaggle-skill
description: Automate Kaggle competition research and notebook workflows. Use when Codex needs to investigate a Kaggle competition from a slug, read public Code/kernels and Discussion topics, archive past editions or similar competitions for prior-art writeups and hot threads, produce a research report, select and reproduce an open baseline, design safe optimization phases, edit or fork notebooks, validate kernel-metadata.json, push Kaggle kernels, monitor runs, pull logs/output, diagnose Kaggle CLI/kernel/submission failures, record leaderboard experiments in an append-only ledger, or manage follow-up monitoring for new Kaggle Code and Discussion content. Trigger on kaggle, Kaggle CLI, competition slug, kernel-metadata.json, kaggle kernels push, Kaggle Notebook, fork notebook, publicScore empty, GBK codec errors, title does not resolve, KernelWorkerStatus, Kaggle Discussion, Kaggle Code research, past editions, prior year competition, similar competition, solution writeup, Nth place solution, experiment ledger, or experiment record.
---

# Kaggle Skill

## Slash Commands

- `/kaggle-research <slug>` — full research pipeline; writes `report.md` + `state.json`
- `/kaggle-past <slug>` — archive past editions and similar competitions
- `/kaggle-fork <owner>/<slug> <work-dir>` — pull, patch, preflight (no auto push)
- `/kaggle-experiment <subcmd> --competition <slug> ...` — append-only experiment ledger
- `/kaggle-watch <slug>` — diff new kernels and discussion topics
- `/kaggle-diagnose <symptom> [--log path]` — match the diagnostics error table

## Core Rules

- Use Kaggle CLI/API capabilities before ad hoc scraping. Use browser access only when the official CLI/API cannot expose required public content.
- On Windows PowerShell, set `$env:PYTHONUTF8=1` and `$env:PYTHONIOENCODING="utf-8"` before Kaggle CLI commands. Never use Bash-style `VAR=value kaggle ...` in PowerShell.
- If `kaggle.exe` exits with no output or crashes on Windows, try `python -m kaggle.cli` from a working Python environment. Bundled scripts should implement this fallback.
- If the installed Kaggle CLI lacks Discussion/topic commands, use Kaggle's read-only JSON API fallback to resolve `forumId`, list topics, and archive selected topic details.
- Treat `kaggle.json` as secret material. Check existence and permissions only; never print the username/key payload.
- Do not consume leaderboard submissions, publish notebooks/datasets, or perform final submission without explicit user confirmation.
- For Kernel-only competitions, do not assume CLI file submission is allowed. Prefer notebook-version submission only when officially supported and still ask before consuming quota.
- Run preflight before kernel push. Run log verification before recommending submission.
- Prefer reproducible baseline replay before optimization. Change one major variable per leaderboard phase.
- Distinguish facts, community claims, and agent inference in reports. Link or archive the source for important conclusions.

## Workflow Selection

- For "research this competition" or a competition slug: read `references/research-pipeline.md`, then run or adapt `scripts/research_competition.py`. Slash command: `/kaggle-research <slug>`.
- For "past editions", "previous year", "similar competition", "Nth place solution", or prior-art lookup: read `references/past-competitions.md`, then run `scripts/past_competitions.py` with `--auto-years`, `--past`, or `--search`. Slash command: `/kaggle-past <slug>`.
- For fork/pull/patch/push/monitor/output flows: read `references/workflow.md`, then use `scripts/preflight_check.py`, `scripts/apply_ipynb_patch.py`, `scripts/monitor_kernel.py`, and `scripts/verify_kernel_log.py` as needed. Slash command: `/kaggle-fork <owner>/<slug> <work-dir>`.
- For recording leaderboard experiments, phase decisions, or rendering an experiment summary: use `scripts/record_experiment.py` (`add` / `update` / `list` / `show` / `report`). See `references/submission-strategy.md`. Slash command: `/kaggle-experiment <subcmd> --competition <slug> ...`.
- For errors such as GBK decode, title/id mismatch, 403, missing submission, timeout, empty publicScore, or KernelWorkerStatus.ERROR: read `references/diagnostics.md`. Slash command: `/kaggle-diagnose <symptom> [--log path]`.
- For watch updates and detecting new public Code/Discussion content: run `scripts/update_research_watch.py`. Slash command: `/kaggle-watch <slug>`.
- For command syntax and safe Kaggle CLI patterns: read `references/kaggle-cli-cheatsheet.md`.

## Research-To-Submission State Machine

1. **Discover**: resolve competition slug, confirm rules access, collect competition metadata, files, rules, metric, deadlines, runtime limits, and submission mode.
2. **Collect**: list public kernels by competition and sort by voteCount, scoreDescending, commentCount, dateRun, and relevance. List Discussion topics and archive selected high-signal topic details.
3. **Past Editions**: when the competition is recurring or sits in a well-studied domain, run `scripts/past_competitions.py` to archive prior-edition or sibling competition metadata, top kernels, and solution writeup threads under `research/<slug>/past/`.
4. **Synthesize**: generate `research/<competition-slug>/report.md` with competition facts, source links, top Code candidates, Discussion signals, cross-edition lessons, constraints, risks, and open questions.
5. **Select**: choose a reproducible baseline using score, recency, comments, output availability, dependency access, code complexity, rule compliance, and expected runtime.
6. **Plan**: write `research/<competition-slug>/optimization_plan.md` with Phase 0 baseline replay and single-variable follow-up phases.
7. **Implement**: fork/pull the baseline, lock metadata, patch notebook/code idempotently, run local static checks, and run preflight.
8. **Run**: push kernel, monitor status, pull output/logs, verify fatal markers, and record the experiment with `scripts/record_experiment.py add`.
9. **Submit Gate**: recommend submission only if output exists, logs are clean, constraints are satisfied, and the user confirms quota use. After scoring, append the result with `record_experiment.py update`.
10. **Watch**: update `research/<competition-slug>/state.json`, then monitor new Code/Discussion content with `scripts/update_research_watch.py`. Re-render the experiment ledger with `record_experiment.py report` at phase boundaries.

## Output Artifacts

- Store research under `research/<competition-slug>/`.
- Use `report.md` for competition research.
- Use `past/` for archived prior-edition and similar competition material.
- Use `optimization_plan.md` for phase design.
- Use `experiments.jsonl` and `experiments.md` for the leaderboard experiment ledger.
- Use `state.json` for monitoring cursors and experiment history.
- Use per-phase directories for pulled/forked kernels and outputs.
