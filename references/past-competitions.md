# Past Editions And Similar Competitions

Use this reference when researching a Kaggle competition and you want to learn from prior editions or sibling competitions in the same domain. Past editions usually expose top-ranked solution writeups, post-mortem discussions, and battle-tested baselines that are far more credible than fresh public kernels on the current edition.

## When To Use

- Annual or recurring competitions (BirdCLEF-YYYY, ISIC-YYYY, RSNA challenges, Kaggle Days events).
- New competitions in a well-studied domain (NLP classification, tabular regression, time-series forecasting, image segmentation, audio recognition).
- Cold-start research where the current competition has few public kernels or quiet discussion.
- Verifying whether a community claim ("ensemble of N models gets gold") matches prior-edition evidence.

Do not use this reference to copy private code or to circumvent the current competition's external-data rules. Past-edition material may include datasets, models, or tricks that are disallowed in the current edition.

## Inputs

- `--past <slug>`: explicit prior or sibling competition slug. Repeatable. Use this when you already know the family.
- `--auto-years` plus optional `--years LO HI`: when the base slug ends in `-YYYY`, expand into earlier years. Example: `birdclef-2026` with `--auto-years --years 2021 2025`.
- `--search <keyword>`: hand off to `kaggle competitions list -s <keyword>` to discover sibling competitions by topic. Repeatable.
- `--include-current`: also archive the base slug itself for parity comparisons.
- `--skip-verify`: skip the visibility precheck. Useful with `--offline` or when the account lacks list access but you still want to attempt archival.

## Output Layout

```
research/<base-slug>/past/
├── index.md            # cross-edition overview table
├── past_state.json     # resolved slugs and run metadata
└── <past-slug>/
    ├── summary.md      # facts + top kernels + solution threads
    └── raw/
        ├── competition.json
        ├── kernels_voteCount.txt
        ├── kernels_scoreDescending.txt
        ├── topics.json
        └── topic_details/<topicId>.json
```

## Workflow

1. From the current competition's `report.md`, decide the search strategy:
   - Year-suffixed family: prefer `--auto-years`.
   - Topical family: prefer `--search` with 2-3 domain keywords.
   - Known siblings: pass `--past` explicitly.
2. Run the script:

```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
python scripts\past_competitions.py <base-slug> --auto-years --years 2021 2025 --topic-details 8
```

3. Read `past/index.md` first. It is the entry point for cross-edition signal.
4. For each archived competition, open `summary.md` and inspect:
   - top-rank solution writeup threads in the **Solution / Hotspot Threads** section
   - `kernels_voteCount` for community-validated baselines
   - `kernels_scoreDescending` for leaderboard-facing kernels
5. Open the corresponding `raw/topic_details/<id>.json` for full discussion text before quoting.

## Solution Thread Heuristics

`past_competitions.py` ranks discussion topics by signal score:

- "1st/2nd/3rd place solution", "winning solution", "writeup", "approach summary" — strongest signal
- Hot keywords like leak, external data, rule, metric, cv, lb, shake, postprocess, ensemble, pseudo, label
- Author marked HOST
- Vote count

Heuristics produce false positives. Always verify by opening the archived JSON.

## Read Across Editions

Before transplanting any trick, ask:

- Is the metric the same? Even small metric changes (macro vs micro F1, primary-only vs full-call) can invert which trick wins.
- Is the data scope the same? Past editions often expose data that the current edition explicitly forbids.
- Is the runtime budget the same? A past-edition winning ensemble may not fit current sandbox limits.
- Is the test scope the same? Hidden-test scoring rules and submission shape often change year over year.

When the answer is "no" or "unclear", record the discrepancy in `report.md` under risks instead of pulling the trick straight into `optimization_plan.md`.

## Combining With Current-Edition Research

Update `research/<base>/report.md` with a "Cross-Edition Lessons" section that points into `past/<slug>/summary.md` files. Keep the current-edition baseline table untouched — past-edition winners are reference material, not direct candidates for `kaggle kernels pull`.

## Refresh

Re-run `past_competitions.py` periodically when the current competition is in early phase. Late-stage solution writeups for *the current* edition will appear in current-edition discussion, not in past editions; use the existing `update_research_watch.py` for those.
