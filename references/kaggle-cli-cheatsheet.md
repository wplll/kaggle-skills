# Kaggle CLI Cheatsheet

Always set UTF-8 in PowerShell before Kaggle commands:

```powershell
$env:PYTHONUTF8=1
$env:PYTHONIOENCODING="utf-8"
```

If the `kaggle.exe` found in PATH crashes with no output, try:

```powershell
python -m kaggle.cli --version
python -m kaggle.cli competitions files <competition> -v
```

Bundled scripts should attempt `kaggle ...` first, then fall back to `sys.executable -m kaggle.cli`.

## Competitions

```powershell
kaggle competitions list -s <search>
kaggle competitions files <competition>
kaggle competitions download <competition> -p data
kaggle competitions submissions <competition>
kaggle competitions submit <competition> -f submission.csv -m "message"
```

Only use `competitions submit` when competition rules allow file submission and the user confirms quota use.

## Competition Discussions

```powershell
kaggle competitions topics list <competition> --sort-by hot
kaggle competitions topics list <competition> --sort-by new
kaggle competitions topics show <competition>/<topic-id>
```

If the local CLI uses older syntax, check `kaggle competitions --help` and adapt to `topic-messages`.

If no Discussion command exists, use the read-only JSON fallback documented in `research-pipeline.md`. Archive raw JSON and clearly label it as an unofficial/internal API fallback.

## Kernels

```powershell
kaggle kernels list --competition <competition> --sort-by voteCount
kaggle kernels list --competition <competition> --sort-by scoreDescending
kaggle kernels list --competition <competition> --sort-by commentCount
kaggle kernels list --competition <competition> --sort-by dateRun
kaggle kernels pull <owner>/<slug> -p <dir> -m
kaggle kernels push -p <dir>
kaggle kernels status <owner>/<slug>
kaggle kernels output <owner>/<slug> -p <out_dir>
kaggle kernels output <owner>/<slug> --version <N> -p <out_dir>
```

## Datasets

```powershell
kaggle datasets files <owner>/<slug>
kaggle datasets download <owner>/<slug> -p data --unzip
kaggle datasets init -p <dir>
kaggle datasets create -p <dir>
kaggle datasets version -p <dir> -m "message"
```

## Models

Kaggle model source access may require browser workspace actions. If CLI cannot verify model access, report the manual check needed instead of assuming availability.
