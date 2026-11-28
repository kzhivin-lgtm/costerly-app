# Labor V3.8: retain Project after late File Review field acknowledgements

Continuation work3.17.4.6. Scope: repair the owner's persistent blank Project
after editing and New Estimate -> Last Estimate -> File Review -> Project.
Preserve V3.5 accepted checkpoint, V3.7 approval/zero/LDSP corrections, saved
data, all navigation/shielding, quantity, pricing, PDF, ownership and auth rules.
No timing optimization, data/schema/model, cache/router or layout change.

## Confirmed mechanism and counterfactual

[verified] File Review metadata/name callbacks assigned screen=file_review on
empty values, deferred Naming echoes and completed save paths. Streamlit1.64
retains widget metadata after the fields unmount. A late widget value arriving
with a Project auto-rerun invokes that old callback before rendering only the
Project fragment. Its guard then sees screen=file_review and returns. Streamlit
clears the fragment's table and its externally owned header/title/stages slots;
the navigation and action buttons outside the fragment remain mounted.

A controlled synthetic native-protocol replay reproduced exactly that blank
page before the patch: injected=true, title=false, table=false, actions=true,
inputs=0. Its screenshot matches the owner's missing-content pattern. This is
not an ordinary slow read, missing saved rows or scroll offset. The production
ready receipt alone did not detect subsequent clearing by a fragment-only run.
[likely] This late-field race explains the owner's report. The exact historical
WebSocket widget payload was not logged and is not claimed recovered.

History supports why the new saved-estimate path exposed this latent callback
bug:5c1af13e introduced the metadata callback navigation in October;40ae800a
(Labor V3.6) enabled the1.5s Project fragment interval for pending saved-Object
preparation as well as live estimation. The accepted V3.5 source only enabled
that interval for live estimation. New Estimate clears Object readiness, so a
restored completed Project now has the timed path used by the reproduction.

The smallest repair removes the five field-callback screen assignments. Existing
navigation button callbacks retain their assignments. Valid field writes/cache
projections, empty rejection, naming CAS/echo handling and actionable errors are
unchanged. The identical single-field browser replay passes after the patch.
No new callback, poll, timer, observer, request or app rerun is added to runtime.

## Verification and publication state

Focused navigation/name checks:77 passed (70 pre-existing plus seven new). Cases cover
metadata/name empty ACKs, accepted edits, failed writes and a Naming echo while
Project remains active. Permanent Navigation additionally exercises New/Last
Estimate reuse and two real native timer messages carrying old field ACKs,
continuous visible title/table/actions, unchanged full-render identity, no empty
writes and complete Object readiness after preparation. Synthetic local data
only; all nonlocal fixture connections remain blocked.
Permanent focused native replay passed16.225s (runner17.397s): two injected ACKs,
continuously visible content, unchanged render identity, no empty writes and
Review ready after release. Initial new-test setup errors (wrong echo fixture
shape and inspecting an outgoing screen before navigation settled) were fixed
without changing runtime, weakening assertions or retrying a failing candidate.

Before-patch replay: /private/tmp/labor38-late-ack-before/.
After-patch replay: /private/tmp/labor38-late-ack-after/.
Earlier simple saved/unsaved/held/fast/deferred-publication replays passed and
were inconclusive, since they omitted the late widget acknowledgement.

Candidate build: labor-v3.8-b20261128150031-project-render-state-detection-v8.4.29.
Full local gate, exact-commit GitHub gate, remote main enforcement, normal
publisher and served/executed Core/wrapper parity remain required. Publication
and owner real-cycle acceptance are not yet claimed. Independent APPROVE/Back/
Last Estimate timing work stays in the authoritative TODO, outside this repair.

Candidate12de4a37 was not published. GitHub run46157860473/job141018368915
passed1231 Python checks, Navigation (including both late ACKs), Calculation
and Project, then failed Profile Save after the390px stored-logo reload: the
preview did not appear within the unchanged10s wait. Official artifact15268516918
(1492077bytes, SHA2568415ac12c1ba67937f3cd1a655f3e5a53b81162e9373a1ba7048f0790d4f360a)
was downloaded and digest/CRC verified. The screenshot is the startup Loading
surface; no server exception was found (the displayed stack is a pre-existing
widget-default warning). The identical clean candidate's complete local Profile
Save passed83.828s, including the reload. Profile code/test assertions and waits
were not changed. The underlying reload-timeout cause remains unknown.

Actions retry is forbidden to both configured GitHub credentials (403), so this
documentation-only evidence commit starts one new cumulative full gate. Runtime
and all tests remain byte-for-byte identical to12de4a37, including the build.
This does not bypass the remote gate or permit publishing the failed candidate.

Full clean local gate on12de4a37 passed618.052s:1231 Python checks and all10
browser suites, including the complete Profile Save83.828s. Its Navigation
artifact records two ACKs and77 consecutive visible title/table/action samples.
The retry candidate05e5bd95 differs only in this evidence document; runtime and
tests are identical. Exact retry GitHub run46158782389/job141021197433 failed
at the same390px Profile-logo assertion after reload. No third unchanged retry
was made. The failure logs are preserved; the underlying timeout cause remains
unknown and is not presented as a Profile runtime repair.

Inspection found that this reload sequence, unlike its own boot() helper,
interacts with Contacts before awaiting the wrapper's ready reveal and Core's
enabled protocol. A controlled delayed-ready local probe did not reproduce the
CI timeout, so its outcome is inconclusive about the historical failure. The
test now explicitly uses the same two startup preconditions as boot() after
reload. This adds readiness checks before the existing interaction; all logo,
exception, persistence, mobile/desktop assertions and their10s waits remain.
No Profile runtime, chooser behavior or product interaction was changed. The
owner reiterated scope: only repair Project, no expansion into a Profile repair.
The complete Profile Save suite with these startup preconditions passed80.428s
(runner81.791s), including all seven existing correlated-ready receipt races.
The release candidate now requires its own exact full local/remote gates; the
earlier two failed GitHub candidates remain unpublished.
