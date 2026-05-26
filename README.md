# kaggle-skills

End-to-end Kaggle competition automation for Claude Code: research a competition from a slug, archive past editions and similar competitions, fork and patch notebooks safely, push and monitor kernels, diagnose failures, and keep an append-only experiment ledger — all surfaced as slash commands.

## Install

### Windows / PowerShell

```powershell
cd <path-to>\kaggle-skills
pwsh -File install.ps1            # user-wide: %USERPROFILE%\.claude
pwsh -File install.ps1 -Force     # overwrite an earlier version
pwsh -File install.ps1 -Scope project  # install into ./.claude in CWD
```

### macOS / Linux / WSL

```bash
cd <path-to>/kaggle-skills
./install.sh                      # user-wide: ~/.claude
./install.sh --force              # overwrite an earlier version
./install.sh --project            # install into ./.claude in CWD
```

After install, restart Claude Code so it picks up the new commands.

### Uninstall

```powershell
pwsh -File uninstall.ps1          # remove from %USERPROFILE%\.claude
pwsh -File uninstall.ps1 -DryRun  # preview only
```

```bash
./uninstall.sh                    # remove from ~/.claude
./uninstall.sh --dry-run          # preview only
```

The uninstaller deletes files one explicit path at a time and only removes directories when they are empty.

## Slash Commands

| Command | Purpose |
|---|---|
| `/kaggle-research <slug>` | Run the full research pipeline; write `report.md`, `state.json`, and `raw/` archives. |
| `/kaggle-past <slug>` | Archive past editions and similar competitions; capture top kernels and Nth-place solution writeups. |
| `/kaggle-fork <owner>/<slug> <work-dir>` | Pull, lock metadata, patch notebook, and run preflight. Never auto-pushes. |
| `/kaggle-experiment <subcmd> --competition <slug> ...` | Append-only experiment ledger. Subcommands: `add`, `update`, `list`, `show`, `report`. |
| `/kaggle-watch <slug>` | Diff new public kernels and discussion topics against the saved watch state. |
| `/kaggle-diagnose <symptom> [--log path]` | Match the symptom against the diagnostics error table and the fatal-marker scan. |

## Typical Flow

```text
/kaggle-research birdclef-2026
/kaggle-past birdclef-2026 --auto-years --years 2021 2025
# pick a baseline from research/birdclef-2026/report.md
/kaggle-fork <owner>/<slug> work/baseline --new-slug me/birdclef-2026-p0 --title "birdclef 2026 p0 baseline"
# after kaggle kernels push
/kaggle-experiment add --competition birdclef-2026 --phase P0 --kernel me/birdclef-2026-p0 --version 1 --status RUNNING
# after run completes
/kaggle-experiment update --competition birdclef-2026 --id exp-001 --status COMPLETE --public-score 0.812
/kaggle-experiment report --competition birdclef-2026
/kaggle-watch birdclef-2026
```

## Output Layout

```
research/<slug>/
├── report.md            # research synthesis
├── state.json           # watch cursors and history
├── experiments.jsonl    # append-only experiment ledger
├── experiments.md       # rendered experiment summary
├── watch_delta.json     # most recent /kaggle-watch diff
├── raw/                 # archived CLI/API outputs
└── past/
    ├── index.md         # cross-edition index
    ├── past_state.json
    └── <slug>/
        ├── summary.md
        └── raw/
            ├── competition.json
            ├── kernels_*.txt
            ├── topics.json
            └── topic_details/<id>.json
```

## Requirements

- Python 3.9+ with the `kaggle` package importable (`python -m kaggle.cli --version` should work).
- A configured `kaggle.json`; the skills never prints its contents.
- On Windows, the install scripts assume PowerShell. Set `$env:PYTHONUTF8=1` and `$env:PYTHONIOENCODING="utf-8"` before manual Kaggle CLI runs.

## Safety

- Never auto-pushes a kernel or auto-submits to the leaderboard. Both require explicit user confirmation per invocation.
- Never modifies `git config` or runs destructive git commands.
- Treats `kaggle.json` as secret material.
- Internal Kaggle JSON endpoints are used only for read-only fallback when the installed CLI lacks Discussion/topic commands; raw responses are archived under `raw/` and labeled.

## Layout in the Repo

```
kaggle-skills/
├── SKILL.md
├── README.md
├── install.ps1
├── install.sh
├── uninstall.ps1
├── uninstall.sh
├── agents/openai.yaml
├── commands/                 # slash-command definitions
│   ├── kaggle-research.md
│   ├── kaggle-past.md
│   ├── kaggle-fork.md
│   ├── kaggle-experiment.md
│   ├── kaggle-watch.md
│   └── kaggle-diagnose.md
├── references/
│   ├── research-pipeline.md
│   ├── past-competitions.md
│   ├── workflow.md
│   ├── kaggle-cli-cheatsheet.md
│   ├── submission-strategy.md
│   └── diagnostics.md
└── scripts/
    ├── research_competition.py
    ├── past_competitions.py
    ├── preflight_check.py
    ├── apply_ipynb_patch.py
    ├── monitor_kernel.py
    ├── verify_kernel_log.py
    ├── update_research_watch.py
    └── record_experiment.py
```
