# Diagnostics

Use this reference when Kaggle CLI, kernel push, kernel run, output retrieval, or submission behavior fails.

## Error Table

| Symptom | Likely Cause | First Check | Fix |
|---|---|---|---|
| `'gbk' codec can't decode byte 0x8b` | Windows codepage decoding compressed response | Confirm PowerShell env vars | Set `PYTHONUTF8=1` and `PYTHONIOENCODING=utf-8` before Kaggle commands |
| `kaggle --version` or any Kaggle command exits nonzero with no output | Broken wrapper or incompatible Anaconda executable | `Get-Command kaggle`; `python -m kaggle.cli --version` | Put a working user Python Scripts path first or call `python -m kaggle.cli` |
| `kaggle competitions: error: invalid choice: 'topics'` | Installed Kaggle CLI lacks Discussion commands | `kaggle competitions --help` | Use `research_competition.py` JSON API fallback or browser/manual access |
| `Your kernel title does not resolve to the specified id` | `title` slug does not match `id` suffix | Run preflight slug check | Use lowercase ASCII title with spaces only |
| `403 Forbidden` | Rules not accepted, private resource, or insufficient permission | Check browser rules page and source access | Accept rules, request access, add to workspace, or remove source |
| `dataset not found` during push | Inaccessible `dataset_sources` entry | `kaggle datasets files <owner>/<slug>` | Add accessible version or remove source |
| `KernelWorkerStatus.ERROR` | Runtime exception, missing path, dependency issue, OOM, timeout | Pull output/log | Scan fatal markers and final log lines |
| COMPLETE but `publicScore` empty | Hidden-test submission failed after notebook completion | `kaggle competitions submissions <competition>` | Pull logs for selected version and inspect timeout/OOM/exception |
| Missing `submission.csv` | Notebook did not write to `/kaggle/working/` or path mismatch | Check output files and notebook write cell | Write `/kaggle/working/submission.csv` |
| `Notebook Timeout` | Runtime exceeds sandbox cap | Runtime markers and competition rules | Reduce inference, disable sidecar, cache, or use lighter model |
| CLI submit rejected for Kernel-only | Competition requires notebook submission | Competition rules and submission command output | Submit notebook version through allowed path |
| Long `QUEUED` | Capacity or accelerator shortage | `kaggle kernels status` | Wait, use CPU, or avoid scarce accelerator |

## Fatal Log Markers

Scan logs with substring matching, not regex JSON slicing:

- `Traceback`
- `RuntimeError`
- `FileNotFoundError`
- `KeyError`
- `CUDA out of memory`
- `Killed`
- `Notebook Timeout`
- `row/column mismatch`
- `submission.csv`

## Empty Public Score

Treat empty `publicScore` as failed scoring until proven otherwise. `SubmissionStatus.COMPLETE` alone is not enough.

Check:

1. Which notebook version was submitted.
2. Whether output exists for that version.
3. Whether hidden-test path differs from dry-run path.
4. Whether runtime exceeded hidden-test budget.
5. Whether logs contain fatal markers.

## Dry-Run Trap

Dry-run may execute on sample data and skip heavy paths. Hidden test may run full inference. If a sidecar or ensemble is optional, add a `REQUIRE=True` mode for submission testing so missing assets or row mismatches become hard failures.

## BirdCLEF 2026 Findings To Generalize

The first real skill test on `birdclef-2026` showed:

- Kaggle competition API can expose important facts such as `onlyAllowKernelSubmissions`, CPU/GPU runtime caps, daily submission caps, required filename, row id column, metric, and `forumId`.
- A high-vote Code table is not enough; also inspect `scoreDescending`, `commentCount`, and `dateRun`.
- Discussion topic titles alone are insufficient; archive selected topic detail JSON before drawing strategy conclusions.
- Preflight should verify dataset sources automatically but model sources often still require manual Kaggle workspace checks.
