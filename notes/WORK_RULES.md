# Costerly Work Rules

These are operating rules for changing the project without repeating avoidable mistakes.

## Debugging Rule

When something breaks, first identify the source of the behavior.

Do:
- compare what changed before and after the regression;
- find the function, state flag, CSS rule, or integration that creates the behavior;
- explain the source in plain language before applying a fix;
- fix the source when possible.

Avoid:
- masking symptoms before understanding the cause;
- adding CSS overlays or extra guards as the first reaction;
- changing unrelated layout, footer, or theme code while the issue is elsewhere.

Short version: source first, symptom second.

## Backup Rule

Before a commit, create a local backup archive in `backups/`.

Do:
- create the backup before `git commit`;
- use the standard exclude list for `.git`, `.venv`, caches, `.streamlit`, `.DS_Store`, and `backups`;
- keep backup archives local only because `backups/` is ignored by git;
- do not inspect or verify archive contents unless there is a specific reason.
- do not ask the user conversationally before routine backup creation; only use a tool approval request if sandbox permissions require it.

Short version: backup first, no archive checking by default.
