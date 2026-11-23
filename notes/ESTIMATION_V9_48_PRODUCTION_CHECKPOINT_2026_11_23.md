# Estimation 9.48, owner-accepted full production checkpoint

Owner reported that both changes worked normally and requested full preservation
on 23 November 2026, existing work reference 3.17.4.6. This checkpoint updates
records, archives and tags only. No new deployment, production write or paid call.

## Exact identities

- Runtime: `862e28f0a848d387f2cf540c34f5769c6a16a3fe`.
- Runtime tag: `estimation-v9.48-production-checkpoint-2026-11-23`.
- Records tag: `estimation-v9.48-checkpoint-records-2026-11-23`.
- Records branch: `codex/estimation-v9.48-prices-labor`.
- Build: `estimation-v9.48-b20261123160825-prices-labor-structure-detection-v8.4.29`.
- Exact-SHA gate: run 45220109273, job 137851749969, artifact 14840671173.
  964 Python checks and ten browser suites passed. Local 420.358s, GitHub 400.189s.
- Core deployment 8005194941 and Cloudflare Pages 48d7b621 succeeded.
  Actual Core, executable wrapper, metadata and version.json matched at
  2026-11-23T16:55:50.500809+00:00, version endpoint HTTP 200.
- GitHub main and active no-bypass ruleset 27499066 were independently rechecked
  before preservation. Main remains on the accepted runtime.

## Accepted result and protected behavior

Prices initially shows closed groups without awaiting all four independent
projections. Closed groups do not construct their rows. The selected open group
renders first, and reopening reuses the ready snapshot. Source library/review/jobs
use the existing asynchronous projection pool; no new poll or worker was added.
Open intent survives count-label changes. Active editors keep their drafts.
Controlled browser evidence on widths 1280 and 390 shows ten selected rows ready
while 290 other rows remain unbuilt and unrelated reads are still pending.

Labor always presents four stages: Part Production, Part Coating, Assembly,
Preparation and Packing. Existing Sheet Processing sits inside Production;
Block Assembly and Additional Assembly sit inside Assembly. Unimplemented new
coating, additional assembly and final preparation/packing show read-only zero.
Existing unknown work is not converted to zero. Existing sheet-processing and
assembly hour keys, editable leaves, payroll, full Self Cost and Overhead remain.
Explicit in-house CNC skips the unused panel-saw alternative in production,
without removing physical assembly. Parts, Material Plan, Detection, catalogs,
provider contracts and all accepted 9.47 interactions remain protected.

Owner acceptance is a production report. It is distinct from the agent's build
marker probe and controlled browser scenarios. No new agent-observed complete
journey through the owner's authenticated account is claimed.

## Version naming decision

The owner intended the next Labor work to use Labor 2.x, mentioned 2.8 as an
approximate number, and deferred resolving it. GitHub already contains historical
Labor 2.8 and 2.9 tags dated 19 November. Do not reuse those tags, retroactively
rename this build, assign a new work block or redeploy just for the label.
Reconcile the exact next Labor minor before the next authorized runtime release.
The deployed build and this immutable checkpoint retain the verified 9.48 identity.

## Archive, evidence and restoration

Private archive:
`/Users/qb/Documents/ChatGPT/Costerly/backups/estimation-v9.48-production-checkpoint-2026-11-23/`

The existing backup helper produced the exact runtime source ZIP: 829 files,
4,742,110 bytes, SHA-256
`9c1014bc6f9843d42477301f483ec6b43f65988dc0651c2073f6324d9d79007f`.
The existing ZIP/LZMA workflow retains the helper's exclusions and 5 MiB cap.
The package contains source inventory, a self-contained Git bundle with separate
runtime/records refs, current project records, full local/CI browser evidence,
the failed candidate and closure-rerender diagnosis, publication/build receipts,
and inherited frozen Parts/input/catalog/purchase controls with provenance.
No credentials, installed dependencies or live database snapshot is included.

A fresh empty-directory restore matched all 829 source files byte for byte.
The verifier checks every manifest hash, the complete file set, ZIP integrity,
self-contained bundle and exact refs. Four restored-source material replays
passed with network blocked: Lev1 29 Parts, Lev2 112, Adda 24/133, saved Lev2
V3.3 110. Their purchase signatures and input immutability match the saved controls.
These are offline controls, not fresh OCR/model or production estimation runs.
The already passing exact-runtime 964/ten gates are reused rather than repeated
for this records-only checkpoint. Final remote refs, records gate and integrity
receipts are pinned in checkpoint.json and outputs/estimation-v9.48/checkpoint-final.json.

```sh
python /path/to/checkpoint/verify_checkpoint.py --restore /new/empty/path --output /outside/checkpoint/restore.json
python /path/to/checkpoint/replay_checkpoint.py --source /new/empty/path
```

Optional `--unit` runs the 964 retained Python checks in the restored source with
the locked application environment. Restore never replaces an existing checkout.
A future rollback requires authorization, an exact-SHA UI gate and matching served
builds. Accepted 9.47 and all earlier immutable checkpoint refs remain intact.

## Deferred work

Agree numerical coating, additional assembly, trial fit and packing boundaries
and rates before activating those calculations. The accepted zero rows do not
claim those operations are estimated yet. Existing Lev1 material/geometry
uncertainties, final UI-contract consolidation and separate unrouted Workers
Builds follow-ups retain their previous status. No new scope is activated here.
