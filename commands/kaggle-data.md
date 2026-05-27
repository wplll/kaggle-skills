---
description: Download Kaggle competition/dataset files or safely create/version a Kaggle Dataset from local files.
argument-hint: "<download-competition|download-dataset|init-upload|create|version|preflight> ..."
allowed-tools: Bash, Read, Write, Edit, Glob, Grep
---

You are managing Kaggle data with arguments `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read `references/data-workflow.md`.
2. Use `scripts/kaggle_data.py` for the requested subcommand:

   ```powershell
   $env:PYTHONUTF8=1
   $env:PYTHONIOENCODING="utf-8"
   python scripts/kaggle_data.py <subcommand> ...
   ```

3. For downloads:
   - Use `download-competition <competition> <out-dir> [--unzip]`.
   - Use `download-dataset <owner>/<slug> <out-dir> [--unzip]`.
   - Do not overwrite extracted files unless the user asked for `--overwrite`.
4. For uploads:
   - Run `preflight <dir>` or `init-upload <dir> --id <owner>/<slug> --title "..."` first.
   - Show the file count, total size, metadata id/title, and warnings.
   - Ask the user for explicit confirmation before `create` or `version`.
   - Invoke `create <dir> --yes` or `version <dir> -m "message" --yes` only after confirmation.
5. Never print `kaggle.json`, never upload credentials, and never make a dataset public unless explicitly requested.

