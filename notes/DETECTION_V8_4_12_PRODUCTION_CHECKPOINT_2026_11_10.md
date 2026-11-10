# Detection V8.4.12 production checkpoint

Release title: Haiku 5.5 · Detection V8.4.12 · Weight short same-sheet Fingerprints.

V8.4.12 is based on the deployed V8.4.11 commit `e902703`. The runtime
change is the short Fingerprint rule from candidate commit `ab0706b`.
The rest of the candidate remains available as a separate development
checkpoint.

Exact matches gain weight when the shorter same-sheet Fingerprint has
two to four dimension positions. The bonus follows the matched fraction
and caps boosted scores at 35. The support threshold stays at 25, and
the dimension-only batch confirmation threshold stays at 40.

On a replay of saved HSL dimension inventories using the release
compiler, Floor 06 gained five supporting pairs. On P06, V1/V2 rose
from 12.8 to 25.6 and V2/V3 from 16 to 32. Floor 07 gained no new
supporting pair. The replay verifies scoring and supporting relations.
Fresh production Upload and the resulting object partition are open.
The dependency pin assertion failed identically on the prior deployed
source and on the release tree.

The Core and Cloudflare build marker is
`detection-v8.4.12-haiku-5.5-short-fingerprint`.
The release tag is `detection-v8.4.12-short-fingerprint-production-2026-11-10`.
The rollback reference is `detection-v8.4.11-before-short-fingerprint-2026-11-10`
at `e902703`.

The private checkpoint is under
`backups/detection-v8.4.12-short-fingerprint-2026-11-10/` in the
Costerly workspace. It holds the Git bundle, source PDFs, frozen OCR
and Membership replies, scoring replay, test output and checksum
manifest. The deployment receipt is stored beside that manifest after
production verification.
