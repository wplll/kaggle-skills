---
description: Pull a Kaggle kernel, lock metadata, run preflight, and prepare it for push (no automatic push).
argument-hint: <owner>/<slug> <work-dir> [--new-slug user/new-slug] [--title "lowercase title"]
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are forking the Kaggle kernel `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/workflow.md` for the fork/patch/push contract and metadata rules.
2. Pull the upstream kernel with metadata:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   kaggle kernels pull <owner>/<slug> -p <work-dir> -m
   ```

   If `kaggle.exe` exits with no output, retry with `python -m kaggle.cli kernels pull ...`.

3. Edit `<work-dir>/kernel-metadata.json`:
   - `id` -> the user's new `<your-user>/<new-slug>` (ask if not supplied)
   - `title` -> lowercase ASCII whose slug equals `<new-slug>`
   - `is_private` -> `true`
   - `competition_sources` -> the target competition slug
   - remove or replace any source the current account cannot access
   - pin reproducibility-critical sources to `/versions/N`
4. Run preflight:

   ```powershell
   python scripts/preflight_check.py <work-dir>/kernel-metadata.json
   ```

   Stop and surface the verdict to the user. Do not push if preflight is `BLOCKED`.
5. If the user wants notebook patches, ask for `cell::before::after` triplets and run:

   ```powershell
   python scripts/apply_ipynb_patch.py <work-dir>/<notebook>.ipynb --patch "CELL::BEFORE::AFTER"
   ```

   Honor idempotency: report applied/already counts.
6. Do **not** run `kaggle kernels push` automatically. Print the exact push command and ask the user to confirm. After confirmation, push, then suggest `/kaggle-experiment add` to record the run.
