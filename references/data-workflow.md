# Data Workflow

Use this reference when the user needs to download Kaggle competition files, download Kaggle datasets, initialize a local directory as a Kaggle Dataset, or upload/version a local dataset.

## Safety Rules

- Treat dataset create/version as publishing or syncing data to Kaggle. Ask for explicit user confirmation before running it.
- Default datasets should be private unless the user explicitly requests public visibility.
- Never print `kaggle.json`.
- Do not overwrite extracted files unless the user explicitly requests it.
- Do not upload secrets, credentials, local cache folders, virtual environments, `.git`, `__pycache__`, or generated logs unless the user explicitly reviewed the file list.
- For competition data, confirm the user has accepted rules. A 403 usually means rules were not accepted or the account lacks access.

## Download Competition Data

Use when the user asks for official competition files:

```powershell
python scripts/kaggle_data.py download-competition <competition-slug> <out-dir> --unzip
```

The script archives the downloaded zip under `<out-dir>` and can extract it safely. If extraction would overwrite files, it blocks unless `--overwrite` is used.

## Download Dataset

Use when the user asks to download a Kaggle Dataset:

```powershell
python scripts/kaggle_data.py download-dataset <owner>/<dataset-slug> <out-dir> --unzip
```

Record the dataset ref and version in research notes when reproducibility matters. Prefer pinned refs such as `<owner>/<slug>/versions/<N>` in kernel metadata.

## Initialize Local Upload

Use when a local directory should become a Kaggle Dataset:

```powershell
python scripts/kaggle_data.py init-upload <dir> --id <owner>/<dataset-slug> --title "dataset title"
```

This writes or updates `dataset-metadata.json` and performs local checks:

- directory exists
- directory has uploadable files
- blocked names are flagged
- id looks like `<owner>/<slug>`
- title slug is compatible with id suffix when possible

## Create Or Version Dataset

Create the first Kaggle Dataset:

```powershell
python scripts/kaggle_data.py create <dir> --yes
```

Publish a new version:

```powershell
python scripts/kaggle_data.py version <dir> -m "describe changes" --yes
```

Use `--public` only if the user explicitly wants a public dataset and competition rules allow publishing it. Otherwise keep it private.

## Preflight Before Upload

Before create/version:

1. Show the metadata id/title.
2. Show file count and total size.
3. Show blocked/suspicious file warnings.
4. Confirm this will upload data to Kaggle.
5. Require `--yes` in the script invocation.

## Typical Use Cases

- Upload trained model weights so a Kaggle notebook can attach them as `dataset_sources`.
- Upload cached features to avoid recomputing expensive inference.
- Download public baseline assets for local inspection.
- Download official competition data for local smoke tests.

