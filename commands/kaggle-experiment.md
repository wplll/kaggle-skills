---
description: Manage the append-only Kaggle experiment ledger (add / update / list / show / report).
argument-hint: <subcmd> --competition <slug> [--phase PN] [--kernel u/s] [--status ...] [...]
allowed-tools: Bash, Read, Write, Edit
---

You are operating the **Kaggle experiment ledger** for arguments `$ARGUMENTS`.

Activate the `kaggle-skill` skill, then:

1. Read the **Experiment Record** section in `references/submission-strategy.md` for the recording discipline (push = record now; status changes = update; failures are evidence; report at phase boundaries).
2. Parse the subcommand from `$ARGUMENTS`. Supported:
   - `add` — append a new experiment. Requires `--phase` and `--competition`.
   - `update` — overlay an existing experiment. Requires `--id` and at least one field.
   - `list` — tabulate experiments. Optional `--phase` filter.
   - `show <id>` — dump merged state and history.
   - `report` — render `experiments.md`.
3. Run:

   ```powershell
   python scripts/record_experiment.py --root research --competition <slug> <subcmd> [flags]
   ```

   Always pass `--root research` (or whatever the user uses) so the ledger lives next to `report.md` and `state.json`.
4. After `add` / `update`, also run `report` so `experiments.md` stays current. After `list` / `show`, just relay the script output.
5. If the user is recording a fresh kernel push, remind them to:
   - capture `--kernel <user>/<slug>` and `--version <N>`
   - set `--status QUEUED` or `RUNNING` initially
   - update the same `--id` with `--status COMPLETE` / `ERROR` and the public score later
6. If the user is recording a submission, treat empty `publicScore` as failed scoring until proven otherwise — record the failure mode if so.
