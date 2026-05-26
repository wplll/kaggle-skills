---
description: Diagnose a Kaggle CLI / kernel / submission failure using the diagnostics reference.
argument-hint: <error-snippet-or-symptom> [--log path/to/run.log] [--kernel u/s]
allowed-tools: Bash, Read, Glob, Grep
---

You are diagnosing a Kaggle failure: `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/diagnostics.md` end-to-end. The error table and fatal-marker list are the authoritative source.
2. If the user provided a kernel reference, fetch its log/output:

   ```powershell
   python scripts/verify_kernel_log.py <user>/<slug> <out-dir>
   ```

   Or scan an existing local log:

   ```powershell
   python scripts/verify_kernel_log.py --log <path-to-log>
   ```

3. Match the symptom against the diagnostics error table. If a row matches, report:
   - **Symptom** verbatim
   - **Likely cause** from the table
   - **First check** to run
   - **Fix** to apply
4. If no row matches:
   - Classify the symptom (CLI error / push error / runtime error / submission error / score anomaly)
   - Apply the dry-run-trap and empty-publicScore checks if relevant
   - Suggest the smallest reproducer
5. Never suggest a fix that bypasses safety:
   - do not run `kaggle competitions submit` without confirmation
   - do not delete files or directories beyond a single explicit path
   - do not modify `git config`
   - do not skip hooks or force push
6. End with a concrete next-action checklist (max 5 items) ranked by reversibility (low risk first).
