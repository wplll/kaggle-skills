---
description: Archive past editions and similar Kaggle competitions; capture top kernels and Nth-place solution writeups.
argument-hint: <base-slug> [--past slug] [--auto-years] [--years LO HI] [--search keyword] [--include-current]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are archiving **past editions and similar competitions** for `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/past-competitions.md` for input rules and the cross-edition transfer checklist.
2. Decide the candidate strategy from the user's arguments:
   - Year-suffixed slug: prefer `--auto-years` (default window = base_year-5..base_year-1, override with `--years LO HI`).
   - Topical family: ask the user for 2-3 keywords if they did not supply `--search`.
   - Known siblings: keep the user's explicit `--past` flags.
3. Run:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   python scripts/past_competitions.py <base-slug> [flags]
   ```

4. Read the generated `research/<base>/past/index.md`. For each archived competition:
   - Open `summary.md` and skim the **Solution / Hotspot Threads** table.
   - For threads with high signal score (>= 100), open the matching `raw/topic_details/<id>.json` and quote the most actionable 1-2 lines.
5. Append a **Cross-Edition Lessons** block to `research/<base>/report.md` if it exists, linking into each `past/<slug>/summary.md`. Do not modify the existing baseline candidate table.
6. Apply the cross-edition transfer checklist before recommending any trick:
   - metric parity
   - data scope and external-data policy
   - runtime budget
   - test/submission shape

   For each "no" or "unclear", record the gap as a risk in `report.md`. Do not promote past-edition winners directly into `optimization_plan.md`.
7. Print a concise summary:
   - archived slugs
   - top 3 transferable insights
   - top 3 cross-edition risks
