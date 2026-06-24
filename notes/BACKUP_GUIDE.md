# Backup Guide

Rules for local project backups. This file exists because backup mistakes are easy to repeat when zip exclude masks are typed by hand.

## Always exclude

- `.git/*`
- `.venv/*`
- `__pycache__/*`
- `*/__pycache__/*`
- `backups/*`
- `.streamlit/*`
- `.DS_Store`
- `*/.DS_Store`

## Safe zip command shape

Always quote every exclude mask so the shell does not expand it before `zip` receives it.

```bash
zip -r backups/VERSION_FOLDER/costerly-app_VERSION_YYYY-MM-DD.zip . \
  -x '.git/*' '.venv/*' '__pycache__/*' '*/__pycache__/*' \
     'backups/*' '.streamlit/*' '.DS_Store' '*/.DS_Store'
```

## Required self-check after every backup

Run this before calling the backup valid:

```bash
unzip -l backups/VERSION_FOLDER/costerly-app_VERSION_YYYY-MM-DD.zip | \
  grep -E '(^|/)(\.git|\.venv|\.streamlit|backups|__pycache__)(/|$)'
```

Expected result: no output. Any output means the archive is invalid and must be deleted and rebuilt.

## Commit rule

Backups are local artifacts and stay ignored by git. Do not `git add -f backups/...` unless the user explicitly asks for that exact archive to be committed.
