# Labor 2.11 full production preservation checkpoint

Owner explicitly requested preservation before Labor 2.12 on24November2026,
work3.17.4.6. This is a complete restorable baseline with known UI limitations.
Preservation does not certify perfect row heights, which the owner disputes.
No runtime change, redeploy, production-data write or new paid model request.

## Exact identities and verified evidence

- Runtime: `63db313d8dbb1e6b8ecec5a05135fe4f2c6d7afc`.
- Source tag: `estimation-labor-v2.11-production-checkpoint-2026-11-24`.
- Records tag: `estimation-labor-v2.11-checkpoint-records-2026-11-24`.
- Records branch: `codex/estimation-v9.48-prices-labor`.
- Build: `labor-v2.11-b20261123213531-disclosure-hours-detection-v8.4.29`.
- Exact-SHA GitHub gate45271419885/job138031904780, artifact14865333744:
  999 Python checks and ten browser suites,346.847s. Full local473.687s.
- Previous release recordsfd46bd80, documentation gate45274046305 succeeded.
- Core deployment8011932973 succeeded. Actual Core, executable wrapper, metadata
  and HTTP200 version.json matched in retained read-only DOM evidence.
  Current main and active/no-bypass main rule27499066 were separately rechecked.
- No newly observed full authenticated production journey is claimed.

## Preserved behavior and known limitations

Four Labor stages, aggregated hours, common Labor/Overhead/Self Cost calculation,
packing and trial-fit norms, old saved manual keys, Save/retry/reopen and zero vs
unknown semantics remain. Expanded aggregate stages hide own metrics and restore
on collapse. Numeric axis checks passed; the owner's new screenshots establish
that equal row heights and gaps need additional verification in2.12.

The preserved2.11 UI has editable Sheet Processing/Block Assembly hours only,
CNC comparison tables and repeated Overhead column headings. User approved2.12
follow-ups are all operational-hour editors, Taxes & Social +25%, equal Labor
row layout, CNC-only labor breakdown without duplicate material/comparison/rate
panels, and one shared Overhead column header. Parent-total editing semantics
are being clarified separately; do not invent inconsistent parent/child totals.

Screenshot witness only (not independently retrieved database amounts): Materials
11,408 ILS, Labor1,767 ILS/28.3h, Overhead1,189 ILS, Self Cost14,363 ILS,
VAT2,585 ILS, total16,948 ILS. All three attached screenshots are preserved.
No precise run/estimate ID is inferred from the cropped UI.

## Archive and restoration

Private archive:
`/Users/qb/Documents/ChatGPT/Costerly/backups/estimation-labor-v2.11-production-checkpoint-2026-11-24/`

Runtime source ZIP835 files,4,771,308 bytes, SHA256:
`a2dcf1bd59b2973528f3d8fbabc17a7b3271ee3856899582e607959a986fad1f`.
Reuse the already helper-validated archive, with its unchanged exclusions and
5MiB cap. Every archived byte matched exact runtime63db313d; a fresh empty-path
restore confirmed835 source files, ZIP integrity and self-contained Git bundle.
Four restored-source material replays match frozen Parts/input/catalog/purchase
controls with network blocked. This is preservation, not a fresh OCR/AI run.

The archive retains exact source inventory, separate runtime/records refs,
project records, successful/failed UI evidence, build/promotion receipts, owner
screenshots, frozen material controls/provenance, restore/replay tools and a
complete SHA256 manifest. Credentials, installed dependencies and live database
snapshots are excluded. Retain previous9.48 and older checkpoints unchanged.

```sh
python /path/to/checkpoint/verify_checkpoint.py --restore /new/empty/path --output /outside/checkpoint/restore.json
python /path/to/checkpoint/replay_checkpoint.py --source /new/empty/path
```

Optional `--unit` runs999 retained Python checks using the locked environment.
Reuse the successful exact-runtime full gates for this records-only preservation.
A future rollback must use the normal exact-SHA gate/publisher and served-build
checks. Final records SHA, remote tag proofs and integrity receipts live in
checkpoint.json and outputs/labor-v2.11-checkpoint-20261124/checkpoint-final.json.
