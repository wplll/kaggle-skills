---
description: Validate a completed Kaggle notebook run and submit a notebook version to a code competition after user confirmation.
argument-hint: "<competition> --kernel <owner>/<slug> --version <N> -m \"message\" [--file submission.csv]"
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are preparing a Kaggle notebook-version submission with arguments `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/workflow.md` and the submission-gate section in `references/submission-strategy.md`.
2. Run validation without `--yes` first:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   python scripts/submit_notebook.py <competition> --kernel <owner>/<slug> --version <N> -m "message"
   ```

3. Confirm the script reports:
   - kernel status is `KernelWorkerStatus.COMPLETE`
   - output pull succeeded
   - `submission.csv` or the requested `--file` exists
   - log verification has no fatal markers
   - it printed the exact `kaggle competitions submit ... -k ... -v ...` command
4. Ask the user explicitly whether to consume a leaderboard submission quota.
5. Only after confirmation, rerun the same command with `--yes`.
6. After submission, suggest recording/updating the run:

   ```powershell
   python scripts/record_experiment.py --competition <competition> update --id <exp-id> --status SUBMITTED
   ```

Never submit when validation fails, when `publicScore`/output is ambiguous, or when the user has not confirmed quota use.
