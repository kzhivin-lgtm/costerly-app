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

## Real Interaction Rule

No product element may be decorative if it implies interaction or database state changes.

Do:
- use real Streamlit/application controls for editable values, actions, approvals, ignores, and navigation;
- persist user edits to the intended state layer or database before downstream flows rely on them;
- clearly explain any temporary non-functional placeholder before adding it.

Avoid:
- rendering fake inputs, fake buttons, or fake toggles for anything the user expects to change;
- replacing implemented functionality with visual imitation to solve a layout or transition problem;
- using decorative HTML controls as a workaround without explicit user approval.

Short version: if it looks editable or actionable, it must actually work.

## Streamlit Transition Rule

Screen-to-screen overlays must account for Streamlit keeping old DOM alive during reruns.

Do:
- replace stale browser event handlers on every rendered screen;
- let the newly rendered current-screen marker clear the overlay after a short stable delay;
- prepare slow data before rendering the new screen header when possible.

Avoid:
- relying on one-time `window` flags for click handlers that must survive repeated navigation;
- using target-screen markers inside the old DOM as proof that the new screen is ready;
- rendering a new header before the data needed for that screen is available.

Short version: repeated navigation must reinstall guards and clear from the current screen.

## Backup Rule

Before a commit, create a local backup archive in `backups/`.

Do:
- create the backup before `git commit`;
- use the standard exclude list for `.git`, `.venv`, caches, `.streamlit`, `.DS_Store`, and `backups`;
- keep backup archives local only because `backups/` is ignored by git;
- do not inspect or verify archive contents unless there is a specific reason.
- do not ask the user conversationally before routine backup creation; only use a tool approval request if sandbox permissions require it.

Short version: backup first, no archive checking by default.
