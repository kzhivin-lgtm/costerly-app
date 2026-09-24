# Auth and Password Recovery Handoff

Date: 2026-09-24
Task: 3.8.2 Password recovery
Status: active and paused for chat migration, implementation preserved, final
production acceptance pending

## Resume here

Work in:
`/Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress`

Branch and remote: `main`, `origin/main`

Do not touch the known untracked `.streamlit/` and `tmp/` paths. Do not create a
branch, fork, worktree, or duplicate project unless the owner asks.

First action in the next chat: confirm that the final HTML and subject were
saved in Supabase, request a new recovery email, inspect it in Gmail iOS dark
mode, then execute the agreed Reset Password matrix below. Do not redesign the
accepted Sign in geometry.

## Mandatory working method

For every interface task, enter scenario-first tester mode before editing:

1. Enumerate all input combinations, actions, validation outcomes, asynchronous
   results, messages, loading states, transitions, and recovery paths.
2. Agree the full matrix with the owner.
3. Implement against the agreed matrix.
4. Give deterministic rows automated regression tests.
5. Execute the same matrix in the real production session.
6. Record unresolved rows explicitly. Do not infer full acceptance from one
   successful happy path.

If testing reveals a missing scenario, update and agree the matrix before
adding another patch. This rule is recorded in `notes/WORK_RULES.md`,
`notes/UI_GUIDELINES.md`, and `notes/ARCHITECTURE.md`.

## Product copy and protected presentation

- Use `Coasterly AI` exactly in user-facing product copy.
- Keep the transactional email sender display name `Coasterly`.
- Omit the final period at the end of a user-facing text block. Preserve periods
  between sentences and meaningful question marks or exclamation marks.
- Do not use the Oxford comma in the password requirement. Current copy:
  `At least 8 characters, one uppercase letter, one lowercase letter and one number`
- Preserve the accepted Sign in geometry: Password and Forgot password share
  the label row, and the password input remains full width below it.
- After a successful recovery request, Forgot password disappears. Sign in
  remains enabled and usable. There is no resend action.

## What is implemented and verified

- Supabase sends recovery mail and the browser handoff reaches Reset password.
- The owner completed a production password change, returned to Sign in, and
  authenticated with the new password.
- Sign in validation handles empty, partial, malformed, wrong-credential, and
  no-company-membership states through the generic credentials response.
- Recovery responses do not reveal whether an account exists.
- Reset validation is ordered: password policy first, confirmation/match second,
  provider update third.
- Duplicate Auth submissions are guarded by the shared loading interaction.
- Recovery email subjects include `{{ .TokenHash }}` so separate requests do
  not thread under one identical Gmail subject.
- Repository email HTML uses the public PNG logo, one flat white surface, no
  nested border or card radius, light-theme guards, and a Gmail iOS blend-mode
  guard for the main paragraph.
- Full automated suite passed: 269 tests.

This does not establish final 3.8.2 acceptance. The latest repository email
template has not yet been visually verified after being copied into Supabase.

## Agreed Sign in contract

| Scenario | Expected result |
| --- | --- |
| Email and password empty, Sign in | Both fields red and `Check your email and password` |
| Valid email, password empty | Password red and the same generic message |
| Password filled, email empty | Email red, password neutral, same generic message |
| Malformed email, password filled | Email red, password neutral, same generic message |
| Email valid, password filled but credentials wrong | Generic message, no provider detail |
| Credentials correct but company access removed | Same generic message and no app access |
| User edits any field after an error | Message disappears; an invalid field clears only when its current value becomes locally valid |
| Enter in Password | Same behavior as Sign in |
| Sign in request running | Trigger button and fields protected from duplicate submission; error restores editing |
| Password visibility control | Shows or hides the password and never submits the form |
| Reset completed successfully | Sign in initially shows `Your password has been updated. Sign in with your new password` |
| Old password after reset | Normal generic credentials error |
| New password after reset | Sign in succeeds if company access exists |

## Agreed Forgot Password contract

| Scenario | Expected result |
| --- | --- |
| Email empty or malformed | Email red and `Enter your email to reset your password` |
| Email valid, account exists | Neutral confirmation: `If an account exists for this email, we sent a password reset link` |
| Email valid, account absent | The identical neutral confirmation |
| Recovery request succeeds | Forgot password disappears; no resend control; Sign in stays usable |
| User clicks or edits email after confirmation | Confirmation remains visible |
| Password contains any value during recovery request | Password is irrelevant and must not remain red because recovery needs only email |

## Agreed Reset Password contract

| Scenario | Expected result |
| --- | --- |
| Valid unused link | Reset password opens with the account email prefilled and disabled |
| Invalid, expired, or already used link | `This password recovery link is invalid or has expired` and `Return to sign in` |
| Both password fields empty | New password red and policy message; Confirm is not evaluated yet |
| New password fails policy, Confirm empty or different | Only the policy error is shown |
| New password passes policy, Confirm empty | Confirm red and `Confirm your password` |
| New password passes policy, Confirm differs | Confirm red and `Passwords do not match` |
| Both values pass and match | One request starts, label becomes `Resetting password...`, fields and trigger are temporarily protected |
| Double click during request | No second provider request |
| Provider accepts update | Return to Sign in and show the password-updated confirmation |
| New password equals the current password | `Choose a password different from your current password` |
| Recovery session expires during editing | Stop loading, unlock the form, and ask for a new recovery link |
| Network or unknown provider failure | Stop loading, unlock the form, preserve input, and show a neutral actionable error |
| User edits after validation error | Dismiss stale text; remove a red state only when that field becomes valid |
| Password visibility control | Toggle visibility without submission |
| Enter in Confirm password | Same behavior as Reset password |

The local policy and the current expected Supabase baseline both require eight
characters, uppercase, lowercase, and a number. A defensive provider weak-
password handler remains because provider policy can change, but it is not a
separate normal acceptance row.

## Supabase email template

Repository body:
`notes/email_templates/password_recovery.html`

Repository subject:
`notes/email_templates/password_recovery.subject.txt`

Subject value:
`Reset your Coasterly AI password [{{ .TokenHash }}]`

The hosted Supabase template is external state. A Git push or Railway deploy
does not update it. Copy the complete repository HTML into Authentication ->
Email Templates -> Reset Password, save it, and generate a new message. Old
messages cannot validate a new template.

Latest Gmail evidence before the flat-template revision:
- the light background and public logo survived Gmail iOS dark mode;
- Gmail inverted the main paragraph to nearly white;
- the nested gray page and rounded bordered white card looked incorrect.

The repository candidate addresses those observations with a flat white
surface and Gmail blend-mode paragraph protection. Production verification is
still pending.

## Important commits

- `dd8eced`: remove password-recovery resend action and add unique subject
- `a09ab51`: fix Auth validation feedback sequence
- `1a78a36`: reject Sign in without company access
- `dd03d64`: keep recovery email in a light palette
- `aa4f328`: flatten and protect the recovery email for Gmail dark mode
- `fa7480f`: remove the Oxford comma from password requirement copy

Preservation backup:
`backups/v3.8.2_password_recovery_chat_handoff/costerly-app_v3.8.2_password_recovery_chat_handoff_2026-09-24.zip`

SHA-256:
`3ad90ecdf3cd24f7cbd0606cee7d6cd5551860a1fad149e90da80d59233d0df6`

## Deployment context

- Railway GitHub autodeploy is enabled on `main`.
- The uv/Railpack deployment checkpoint is `bf0581d`.
- The observed Railway deployment duration is about three minutes. The app can
  be tested after Railway reports success and `app.costerly.ai` serves the new
  build.
- Supabase template changes are independent of Railway deployment.

## Ordered backlog

1. P0, actionable: save the final subject and HTML in Supabase and generate a
   new recovery message.
2. P0, actionable: verify Gmail iOS dark mode, desktop Gmail, logo, paragraph,
   flat white background, button, footer, and separate subject threading.
3. P0, actionable: execute every agreed Reset Password row in production and
   record pass/fail without redesigning Sign in.
4. P0, actionable after failures are known: fix only failed rows, update the
   matrix first if a previously unknown state appears, rerun automated tests,
   deploy, and repeat the affected plus protected rows.
5. P0, pending final pass: establish and archive the accepted 3.8.2 production
   checkpoint with backup hash, Done Log, commit/push, remote equality, and
   production confirmation.
6. P0, pending: current-project two-company isolation verification.
7. P1, pending: confirm-email and broader production email policy for future
   notifications, invoices, reminders, and transactional messages.

## Verification commands

```bash
cd /Users/qb/Documents/Codex/2026-07-17/detection-gpt-detection-agent-ocr-gpt/work/costerly-progress
.venv/bin/python -m pytest -q
git diff --check
git status --short
git rev-parse HEAD
git ls-remote origin refs/heads/main
```

Production acceptance must use `https://app.costerly.ai/` in the owner's real
browser and mail sessions. Source inspection, tests, a direct Railway URL, or a
new unauthenticated browser tab are not substitutes.
