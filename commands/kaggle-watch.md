---
description: Refresh Kaggle research watch; diff new public kernels and discussion topics; update report.
argument-hint: <competition-slug> [--offline]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are refreshing the **Kaggle research watch** for `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Confirm `research/<slug>/state.json` exists. If not, instruct the user to run `/kaggle-research <slug>` first.
2. Run:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   python scripts/update_research_watch.py <slug>
   ```

3. Read `research/<slug>/watch_delta.json`:
   - For each new kernel ref, fetch its metadata and decide if it changes the baseline ranking.
   - For each new topic id, open the matching archive (or refetch the detail JSON) and classify it: host clarification / rule change / metric insight / CV-LB mismatch / leak / shared trick / failure mode / resource issue / speculation.
4. Update `research/<slug>/report.md`:
   - Append findings under a **Watch Updates** section dated today.
   - Mark compliance-sensitive items for user review.
   - Do not rewrite the baseline candidate table without user confirmation.
5. If new content suggests a different baseline or a new optimization phase:
   - Surface the proposed change to the user.
   - Do not edit `optimization_plan.md` or push any kernel without confirmation.
6. Print a concise summary:
   - count of new kernels and new topics
   - top 3 changes that would affect the baseline or the plan
   - any leak / rule / metric claims that need user review
