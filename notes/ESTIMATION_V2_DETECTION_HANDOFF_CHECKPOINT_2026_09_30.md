# Estimation v2 Detection handoff checkpoint, 2026-09-30

Task: 3.15.8. Backend foundation only. File Review, Objects, Object Detail,
CSS and production remain unchanged.

## Completed and verified

- private original-file contract, SHA-256 audit identity and Storage ref;
- private evidence artifact and immutable object-input schema migrations;
- `estimation_input_v2` pure builder, strict OCR anchor-to-bbox validation and
  source-derived WebP cropper;
- Detection optional `evidence_page_refs` and `evidence_anchors` contract;
- synchronous repository primitive that returns `ocr_event_id`.

The original file is retained privately. Hash reuse across different runs is
not implemented yet and must not be claimed as current behavior.

## Verification

13 targeted tests passed, `py_compile db/repositories.py` passed, and
`git diff --check` passed.

## Shadow handoff completed after this checkpoint

The backend shadow vertical slice is now wired: Detection persists the original
in parallel and one synchronous OCR event; after File Review edits, the
background estimation job resolves an exact OCR anchor, renders the source
page, uploads a WebP preview, and persists the immutable input revision plus
artifact metadata. Invalid or missing evidence skips only the v2 shadow input
and does not break the legacy UI flow.

## Remaining before first real production acceptance

1. Apply the additive SQL migrations, then run one real authenticated PDF
   through Detection in shadow mode and verify one OCR call, private original,
   correct preview, refresh, company isolation, and unchanged UI.
