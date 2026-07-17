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

## Dependency Reuse Rule

If the project already has a suitable dependency, or a mature open implementation exists on GitHub/npm/PyPI, prefer using it directly instead of rebuilding the same behavior from scratch.

Do:
- check existing project dependencies and local helpers before writing custom implementations;
- consider mature open-source libraries for established UI behavior, parsing, exports, rules engines, math, and integrations;
- before adding a new dependency, briefly check maintenance, license, package size, and compatibility with the project.

Avoid:
- hand-rolling established behavior when a supported library fits the job;
- adding a dependency without checking whether the project already has an equivalent tool;
- choosing a library only because it is convenient if its license, bundle/runtime cost, or maintenance status is unclear.

Short version: reuse mature tools first, but verify fit before adding dependencies.

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

## Local Verification Before Push Rule

Changes that affect UI, browser JavaScript, uploads, timers, navigation, screen transitions, or asynchronous state must be manually verified in the local browser before they are committed or pushed.

Required sequence:
- implement the change locally;
- run automated tests and syntax checks;
- close old local ports and start the single current local port;
- open the updated local app in Chrome;
- wait for the user to manually verify both the requested behavior and the surrounding flow;
- only after explicit user confirmation, create the backup, commit, and push.

Automated tests, compilation, and code inspection do not replace manual browser verification for interactive behavior.

If local verification exposes a regression, fix it locally and repeat the full manual check. Do not push an unverified hotfix merely because the previous version is already on production.

Short version: local browser confirmation first; backup, commit, and push only after.

## Backup Rule

Before a commit, create a local backup archive in `backups/`.

Do:
- create the backup before `git commit`;
- create backups only with `.venv/bin/python tools/create_backup.py VERSION SLUG`;
- let the backup helper validate exclusions and archive size before accepting the backup;
- keep backup archives local only because `backups/` is ignored by git;
- do not ask the user conversationally before routine backup creation; only use a tool approval request if sandbox permissions require it.

Avoid:
- hand-writing `zip -r` backup commands;
- accepting a backup that has not passed helper validation;
- deleting and recreating an invalid backup without explaining the validation failure.

Short version: backup first, helper only, validation required.
