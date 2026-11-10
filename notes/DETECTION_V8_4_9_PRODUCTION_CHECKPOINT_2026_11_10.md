# Detection V8.4.9 production release checkpoint

The owner requested deployment of the regular Upload path after a full
checkpoint. Runtime is the post-cleanup V8.4.9 tree at `0ddbc66`.
The release commit changes the visible build markers and records the
checkpoint. The previous production ref is
`detection-v8.4.7-before-v8.4.9-deploy-2026-11-10` at `8eb87f1`.

The runtime enables the V8.4.8 Ada Sonnet Membership flow and V8.4.9 Haiku
5.5 plus local coordinate OCR. Coordinate OCR is recorded alongside
existing evidence. Production Membership still uses the established
merge path. See the [coordinate OCR record](DETECTION_V8_4_9_HAIKU_COORDINATE_OCR_2026_11_10.md).

Exact fixed-input replays matched Adda, Lev 1, Lev 2, HSL 07, and both
Page 23 paths. The HSL 07 production-path witness had 30 groups. The
owner-accepted ten-group experiment is preserved as a separate Git ref.
The release regression subset had 338 passes and the existing Processing
completion-marker test failure. Its implementation and test match the
previous production commit.

Full private checkpoint: `backups/detection-v8.4.9-full-checkpoint-2026-11-10/private-full-detection-checkpoint.tar.gz`
in the Costerly workspace. Archive SHA-256:
`451e67b67b4a105d4fd221ddacf8f4e941ba7126bd3d2e003b517011927cf23f`.
Restored all 425 entries by checksum and cloned the experimental
`detection-v8.4.9-full-lab-2026-11-10` tag at `b5b7712` from the bundle.
The two original HSL PDFs, fresh provider replies, audit scripts, and
protected replay packs stay in the private archive.

## Deployment names

Use `<model and version> · Detection <current version> · <latest change>`
in the visible deployment title and the corresponding release commit title.
Name the model used by the affected route. Carry the same three fields in
the machine-readable build marker.
Write deployment titles, commit messages, code comments, and project
records in English.

Example: `Haiku 5.5 · Detection V8.4.9 · Processing timer recovery`
