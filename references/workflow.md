# Notebook Workflow

Use this reference for Kaggle notebook pull, fork, patch, metadata validation, push, status monitoring, output retrieval, and log verification.

## Minimal Fork Flow

1. Pull upstream:

```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
kaggle kernels pull <owner>/<slug> -p <work_dir> -m
```

2. Edit `kernel-metadata.json`:

- `id`: `<your-user>/<new-slug>`
- `title`: lowercase ASCII words whose slug matches `<new-slug>`
- `is_private`: `true`
- `competition_sources`: target competition slug
- remove or replace inaccessible sources
- pin important sources to `/versions/N` when reproducibility matters

3. Patch notebook/code:

- Use JSON-aware notebook patching for `.ipynb`.
- Prefer `scripts/apply_ipynb_patch.py` for cell source replacements.
- Fail when anchors are missing.

4. Preflight:

```powershell
python scripts/preflight_check.py <work_dir>\kernel-metadata.json
```

5. Push:

```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
kaggle kernels push -p <work_dir>
```

6. Monitor:

```powershell
python scripts/monitor_kernel.py <user>/<slug>
```

7. Pull output and verify:

```powershell
python scripts/verify_kernel_log.py <user>/<slug> <work_dir>\output
```

8. Submit a completed notebook version only after user confirmation:

```powershell
python scripts/submit_notebook.py <competition> --kernel <user>/<slug> --version <N> -m "message"
# If validation is clean and the user confirms quota use:
python scripts/submit_notebook.py <competition> --kernel <user>/<slug> --version <N> -m "message" --yes
```

## Metadata Rules

- `title` must slugify to the `id` suffix.
- Avoid punctuation, plus signs, dots, and uppercase in titles.
- `is_private` should be true for experiments unless the user explicitly wants public release.
- `enable_internet`, `enable_gpu`, and accelerators must match competition rules.
- Sources must be accessible to the current account.

## Notebook Editing Rules

- Do not manually edit raw `.ipynb` cell JSON for nontrivial changes.
- Do not silently skip missing anchors.
- Preserve notebook JSON validity.
- Make patchers idempotent.
- Print applied/already counts for later verification.

## Output Rules

`kaggle kernels output <slug>` retrieves artifacts from the latest completed/successful version by default. Use `--version <N>` when a specific version matters.

Expected competition output usually includes `/kaggle/working/submission.csv`. If missing, inspect log and notebook write paths before submission.

## Notebook Version Submission

Kaggle CLI supports notebook-version submission for code competitions:

```powershell
kaggle competitions submit <competition> -k <user>/<notebook-slug> -f submission.csv -v <version> -m "message"
```

Before running it:

- require `KernelWorkerStatus.COMPLETE`
- pull output for the target version
- verify logs for fatal markers
- verify the output file exists
- ask the user before consuming quota
