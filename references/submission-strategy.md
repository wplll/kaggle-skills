# Submission Strategy

Use this reference for leaderboard experiments, baseline replay, sidecar risk, hidden-test safety, and final selection.

## Discipline

- Phase 0 must replay the selected baseline with minimal code changes.
- Change one major variable per leaderboard phase.
- Record failed submissions; failures are evidence.
- Do not optimize from an unreproduced baseline.
- Do not spend LB quota without explicit user confirmation.

## Experiment Record

Use `scripts/record_experiment.py` for an append-only ledger under `research/<competition>/experiments.jsonl`. Render `experiments.md` at phase boundaries.

Record fields:

- phase
- competition
- kernel slug
- notebook version
- code delta
- metadata delta
- validation markers
- status
- publicScore
- failure mode
- decision

Common usage:

```powershell
python scripts\record_experiment.py --competition <slug> add `
  --phase P0 --kernel <user>/<slug> --version 3 `
  --code-delta "replay only" --status COMPLETE `
  --public-score 0.812 --decision keep --notes "baseline replay clean"

python scripts\record_experiment.py --competition <slug> update `
  --id exp-001 --status SUBMITTED --public-score 0.815

python scripts\record_experiment.py --competition <slug> list
python scripts\record_experiment.py --competition <slug> show exp-001
python scripts\record_experiment.py --competition <slug> report
```

Rules:

- Add an entry the moment a kernel is pushed; do not wait for scoring.
- Update the same entry as status, publicScore, and decision change. Never rewrite history; the ledger is append-only.
- Failed runs and rejected submissions are evidence — record them with the failure mode and decision.
- Run `report` at every phase boundary so the rendered `experiments.md` stays close to the leaderboard state.

## Sidecar And Ensemble Risk

For each added model or sidecar:

- verify source access
- estimate runtime independently
- verify row_id construction shares the same source as the anchor
- add markers for applied/skipped/fallback paths
- add `REQUIRE=True` for submission-critical components

## Hidden-Test Risk

Dry-run success does not prove hidden-test safety. Estimate:

```text
anchor_runtime + per_item_runtime * hidden_item_count <= sandbox_cap
```

If hidden count is unknown, use competition discussion estimates and conservative margins.

## Final Selection

Use final slots for genuinely different risk profiles:

- safe pole: robust consensus or lower variance
- diverse pole: structurally different model/data/feature path

Avoid spending two final slots on same-structure variants unless evidence says variance is low and one dominates.

