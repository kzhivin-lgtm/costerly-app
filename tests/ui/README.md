# Persistent UI release contract

These checks exercise production Streamlit screens and the Cloudflare wrapper
against synthetic local data. They make no paid model call and cannot write
to production services. `app_fixture.py` rejects nonlocal socket connections.
The synthetic saved bench costs ILS 1,000; this is an interaction fixture,
not a fresh Lev1 material or labor benchmark. The private V1.3.3 archive
retains the real saved controls and their evidence.

The protected behavior is defined in `notes/UI_GUIDELINES.md`. The four suites
cover 54 normal transitions across desktop/mobile and an older open wrapper,
Save/reopen in seven Profile paths, preload/read reuse, keyboard, actor access,
expired auth, handled read/write failures, timeout/double click and recovery.
Python checks cover the navigation/state/cache contracts and release verifier.
They also cover UI view priority, unchanged Naming selection, crop persistence,
tenant/run/object ownership and Calculation inheritance. Navigation asserts
that File Review and the reopened saved card display the same synthetic crop.

## Run

From the repository root, with uv and Node 24:

```sh
uv sync --locked --group ui-test --no-install-project
npm ci --prefix tests/ui --ignore-scripts
tests/ui/node_modules/.bin/playwright install chromium
uv run --locked --group ui-test python tools/run_ui_contract.py
```

Linux CI installs Chromium system dependencies with `playwright install
--with-deps chromium`. An existing Chrome can be selected with
`COSTERLY_CHROME=/absolute/path/to/chrome`. Ports 8789, 8796 and 8797 must be
free. Each browser suite receives a fresh server and synthetic database;
cache behavior within a suite is still exercised normally.

`.ui-artifacts/gate-report.json` records the tested commit, outcome, stage
durations and total test execution time. CI uploads logs, reports and local
fixture state for 14 days even when a check fails. CI job setup/download time
is additional and must be reported separately from the test execution time.

## Publication boundary

`.github/workflows/ui-contract.yml` produces `UI release gate` on candidate
branches. Its final verification cannot pass after a failed or skipped full
run. Ordinary Markdown records in `notes/` and root README can use the short
path; the behavior contract, tests, workflows, dependencies and all other
source changes require the full run. Planning compares the whole candidate
against production main, so a docs follow-up cannot erase a failed source diff.

The remote ruleset in `.github/ui-release-ruleset.json` must also be installed
and active. It requires the check from GitHub Actions (integration 15368),
has no bypass actors, and protects main plus a non-production canary branch.
Without that repository setting, CI reports a result but cannot prevent an
arbitrary direct push. Existing credentials may need a one-time administrator
action; never broaden the production app token for this purpose.

Review the template with:

```sh
uv run --locked --group ui-test python tools/configure_ui_gate.py
uv run --locked --group ui-test python tools/configure_ui_gate.py --verify
```

An administrator can import the JSON ruleset in GitHub, or run the installer
with a dedicated local `GITHUB_ADMIN_TOKEN` and `--apply`. Never paste tokens
into chat, commit them or pass them as command-line arguments.

After the exact commit passes CI:

```sh
uv run --locked --group ui-test python tools/promote_ui_release.py COMMIT
uv run --locked --group ui-test python tools/promote_ui_release.py COMMIT --publish
```

The publisher requires both a trusted success for that SHA and the active
remote ruleset before touching main. Core and the production wrapper then
consume the same checked commit; no new UI run is triggered just by promotion
to main or the protected canary.

## Prove failure blocks publication

Use an isolated development branch to break a real navigation path, run the
same check and retain its failure report. Attempt publication verification
for that SHA and require rejection. With the remote ruleset active, also try
the failed SHA against `codex/ui-release-gate-canary`, never production main.
The canary ref must remain on its previous successful commit. Revert the
experimental source change and preserve the failed-commit reference and
rejection evidence. A failing assertion added only to the test does not prove
that the suite detects a broken transition.
