---
description: Run end-to-end Kaggle competition research from a slug; produce report.md, state.json, and source archives.
argument-hint: <competition-slug> [--page-size N] [--topic-details N] [--offline]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are running the **Kaggle research pipeline** for slug `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/research-pipeline.md` for the full pipeline contract.
2. Run `scripts/research_competition.py` with the provided slug and any extra flags from `$ARGUMENTS`. Use PowerShell-safe invocation:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   python scripts/research_competition.py <slug> [--page-size N] [--topic-details N] [--offline]
   ```

3. After the script writes `research/<slug>/report.md` and `state.json`, read both and:
   - Verify the API competition fact table is populated. If `forumId` is missing, surface that to the user as a warning.
   - Cross-read the top kernel candidates and discussion topic details to fill the **Baseline Recommendation** and **Optimization Opportunities** sections that the script left as placeholders.
   - Promote any rule, metric, leak, or runtime claims from `raw/topic_details/*.json` into the **Risks And Blockers** section.
4. Do not pull, fork, push, or submit anything. Research is read-only.
5. Print a concise summary back to the user:
   - top 3 baseline candidates with reasons
   - top 3 risk/blocker items
   - paths to `report.md` and `state.json`

If the competition slug looks year-suffixed (e.g. `birdclef-2026`) or sits in a recurring domain, end with: "Run `/kaggle-past <slug>` next to archive prior editions."
