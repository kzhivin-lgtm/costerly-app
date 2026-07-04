# Backup Guide

Rules for local project backups. This file exists because backup mistakes are easy to repeat when zip exclude masks are typed by hand.

## Required command

Always create backups through the validated helper:

```bash
.venv/bin/python tools/create_backup.py vX.Y.Z before_task_name
```

Do not create backups with a hand-written `zip -r` command. The helper owns archive naming, exclusions, validation, and cleanup after failed validation.

## Helper validation

The helper must reject and delete the archive if any of these checks fail:

- no `.git/` paths inside the archive;
- no `.venv/` paths inside the archive;
- no `backups/` paths inside the archive;
- no `.streamlit/`, `__pycache__`, or `.DS_Store` paths inside the archive;
- `app.py` is present;
- `notes/DONE_LOG.md` is present;
- archive size is not suspiciously large.

## Always exclude

- `.git/*`
- `.venv/*`
- `__pycache__/*`
- `*/__pycache__/*`
- `backups/*`
- `.streamlit/*`
- `.DS_Store`
- `*/.DS_Store`

## Legacy zip command shape

This command is kept only as historical reference. Do not use it for routine backups; use `tools/create_backup.py`.

```bash
zip -r backups/VERSION_FOLDER/costerly-app_VERSION_YYYY-MM-DD.zip . \
  -x '.git/*' '.venv/*' '__pycache__/*' '*/__pycache__/*' \
     'backups/*' '.streamlit/*' '.DS_Store' '*/.DS_Store'
```

## Required self-check after every backup

The helper runs validation automatically. If a manual archive is ever explicitly requested, run this before calling the backup valid:

```bash
unzip -l backups/VERSION_FOLDER/costerly-app_VERSION_YYYY-MM-DD.zip | \
  grep -E '(^|/)(\.git|\.venv|\.streamlit|backups|__pycache__)(/|$)'
```

Expected result: no output. Any output means the archive is invalid and must be deleted and rebuilt through `tools/create_backup.py`.

## Commit rule

Backups are local artifacts and stay ignored by git. Do not `git add -f backups/...` unless the user explicitly asks for that exact archive to be committed.
