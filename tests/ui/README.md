# Persistent UI release contract

These checks exercise production Streamlit screens and the Cloudflare wrapper
against synthetic local data. They make no paid model call and cannot write
to production services. `app_fixture.py` rejects nonlocal socket connections.
The synthetic saved bench costs ILS 1,000; this is an interaction fixture,
not a fresh Lev1 material or labor benchmark. The private V1.3.3 archive
retains the real saved controls and their evidence.

The protected behavior is defined in `notes/UI_GUIDELINES.md`. The nine suites
cover the page/header/footer/Profile transition matrix across desktop/mobile and safe migration of an older open wrapper,
Save/reopen in seven Profile paths, preload/read reuse, keyboard, actor access,
expired auth, handled read/write failures, timeout/double click and recovery.
Python checks cover the navigation/state/cache contracts and release verifier.
They also cover UI view priority, unchanged Naming selection, crop persistence,
tenant/run/object ownership and Calculation inheritance.
Calculation additionally covers a delayed new-estimate shell, full reruns during
progress and after completion, one pricing table, editable Sheet Processing and
Assembly hours, whole grouped money, failed Save/retry and persisted reopen.
These checks use synthetic data and do not establish production acceptance.
The version-refresh suite uses the real wrapper and workflow controller with
synthetic screens. V2.9 covers a single Core build event, old-tab migration,
one reload, deferred active work, failure recovery and zero version-file reads.
The auth-resume suite additionally uses production server auth, ready and
browser persistence code with stateful single-use synthetic refresh tokens.
It advances expiry twice, rotates each token, triggers automatic outer reload
and verifies login in each new server session; genuine revocation still reaches
Login. It rejects nonlocal socket IO. This is stronger than storing token bytes,
but remains distinct from owner production acceptance. It also covers the real
sign_in callback followed by a version reload and a used stale cookie with a
newer valid tab session; rejected tab sessions still reach Login.
Navigation asserts
that File Review and the reopened saved card display the same synthetic crop.

Compatibility recovery uses the exact published V1.2.23 wrapper (582343a),
an absent ACK and an unsupported protocol. Native page/tab callbacks must not
run without confirmed protection. A user-activated top link updates even the
pre-protocol shell, retains browser session storage and restores normal covered
navigation. Cancelled confirmation retains edits; active uploads/calculations
block reload. The existing telemetry records protocol ACK and cover start/end,
and click/ready records explicitly say whether the route was covered.

Objects V2.3 adds a V2.2 geometry witness at1440/2536 desktop widths. It verifies
fixed title/table/object rows/totals/footer, service-field boundary clicks at
1/4/8px on all four sides, inside-field editing/persistence, equal stage lines,
document-heading axes and the existing PDF URL. Local metrics folding must not
rerun/read/write, survives markup replacement and full navigation, and remains
restricted to the already-loaded platform-admin visibility. V2.2 compatibility,
authentication and transition suites stay obligatory and unchanged.
Fixed coordinates and dimensions remain strict. The intrinsically sized VAT
box alone uses frozen V2.2 typography rendered on the current platform, rather
than requiring Linux system fonts to have macOS glyph widths.

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
`COSTERLY_CHROME=/absolute/path/to/chrome`. Ports 8789, 8796, 8797 and 8798 must be
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

## Explicit V1.2.23 rollback

On 20 November 2026 the owner approved the exact historical runtime rollback.
When `.github/approved-rollback.json` is present, the same required CI workflow
and publisher invoke `tools/run_legacy_rollback.py` through the usual runner.
The gate checks every runtime source and locked runtime dependency against
`582343a1`, permitting only synchronized wrapper metadata and version.json.
It runs the unchanged original regression assertions and current publication
protection tests. The modern suites above remain unchanged and resume when the
manifest is removed. Their newer behavior is intentionally absent from V1.2.23;
a successful rollback check does not claim those suites or fresh Ada pass.

The first local historical run passed 567 checks and exposed one stale
dependency expectation already present in the target commit: it omitted ONNX
pins and expected different pandas/Pillow versions. The literal assertion was
corrected to the unchanged target pyproject/lock, preserving exact-pin checks.
No runtime dependency was changed to satisfy that test.

The owner subsequently approved the V1.2.21 source `c84ece4c` on the same date.
The manifest and strict source check now pin that version. Its original
regression suite omits `test_block_assembly.py`, because neither the feature nor
that test existed in V1.2.21. The newer test file is retained in the repository
for subsequent restoration. Original V1.2.21 Sheet Processing/CNC, material,
auth, route, persistence and observability checks plus publication protection
remain required. No present-day recognition stability is inferred from CI.

## V3.2 modern runtime restored

On20November2026 the owner approved V3.2 from the modern V3.1 base. The
temporary approved-rollback.json is removed and the ordinary full runner is
active again. Historical diagnostic-gate tests read their pinned7d631d35 fixture,
not today's runtime. The normal mandatory gate additionally covers native arrow
contact, contour-owned label transcription, complete source coverage, preserved
raw diagnostics and the dependent Parts/geometry/material contracts. The legacy
rollback sections above describe history, not the active V3.2 publication path.

## Objects V2 interface,21November2026

The owner approved the desktop header/footer contract in
`notes/OBJECTS_V2_UI_CONTRACT_2026_11_21.md`. The eighth browser suite exercises
real saved Review/Approve navigation, three equal footer actions, the24px metric
gap, unchanged162px project-cost inputs, original price persistence, edits after
confirmation, generation failure/retry and the latest-price
proposal snapshot. It waits for correlated app-ready before editing. Synthetic
PDF/storage responses remain separate from owner production acceptance.

## Continuous navigation coverage after document restoration

The navigation suite includes fresh, migrated old-wrapper, mobile and restored
Core-document cases. The restored case performs two real iframe document
navigations without obs_trace, then exercises header destinations from Upload,
File Review, Objects, Object Detail, Projects and Profile, all eight Profile
tabs, footer Back/Approve and sign-out. Profile/Objects reads are delayed.
Every pending frame must remain covered until the correlated Core-ready emit
time; Profile tabs retain their accepted regional cover/header. Admin-entry
latency optimization remains deferred. A nonempty sampled interval is required,
so a missing ready timestamp cannot vacuously pass. No input mechanics change.
