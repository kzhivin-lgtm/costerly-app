# Detection V6.23 Naming audit checkpoint, 2026-10-26

## Scope and protected checkpoint

- Commit: `c990495`, `feat(detection-v6.23): bound OCR and quantity review`.
- Production branch: `main` received this commit before the audited run.
- Run: `run_f25514b2332540d1ac58b8b84ea5f7ec`.
- File: `Hasolelim_Carpentry_Plan_Floor_07.pdf`, 11 source pages.
- Protected behaviour: V6.23 removes the per-page title-block OCR fallback;
  title facts come only from ordinary OCR/Fusion. It retains V6.22 Naming
  source crops and Kitchen category evidence. File Review reduces a quantity
  review warning to a red `QTY` label.

This is a measured checkpoint, not an acceptance of the final names as a
quality result. Do not make a further Naming change without an approved next
experiment.

## Verified performance result

| Stage | V6.21 baseline | V6.22 | V6.23 |
| --- | ---: | ---: | ---: |
| OCR page count | 11 | 17 | 11 |
| OCR cost | $0.044000 | $0.068000 | $0.044000 |
| Detection cost | $0.151403 | $0.158499 | $0.160079 |
| Naming cost | $0.026885 | $0.030180 | $0.029424 |
| Measured total | $0.222288 | $0.256679 | $0.233503 |
| Initial processing cycle | 88.018 s | 130.959 s | 72.243 s |

V6.23 removed the six sequential title-block OCR requests that caused the
V6.22 cost and latency spike. It is $0.023176 cheaper and 58.716 seconds
faster than V6.22 on this run. It remains $0.011215 above the V6.21 measured
total, chiefly because the retained grounded Naming call is still more
expensive than V6.21.

## Verified Naming result

The model's returned Naming decision was semantically better than the final UI
names for six kitchen objects. It returned `Kitchen` on objects 002 and
004-008, each with page-local visual rationale citing a cooktop and sink.
However, the Naming validation rejected all six with
`kitchen_cue_not_allowed`, so File Review retained the prior technical labels:
`N57`, `N62`, `N68`, `N70`, `Object 07`, and `N76`.

The direct cause is a contract contradiction:

1. The model schema lets `category_evidence.cue` be free text, and the prompt
   permits it to explain the visual cue.
2. The runtime accepts Kitchen only when that same field exactly equals one
   of a short enum-like set such as `sink`, `cooktop`, or `microwave`.
3. The model returned a useful phrase, for example `Cooktop and sink
   integrated into cabinet system`, which therefore failed validation.

The current validator also checks only that `visual_group_id` is nonempty. In
the audited response it contains `object-002` style object ids, not verified
Registry View ids. Therefore the V6.22 evidence boundary is not yet grounded
enough to support a quality claim.

The remaining final names include `Shelving unit`, `N60 Shelving unit`,
`N76B Stair railing`, and `N76B Shelving unit`. This checkpoint does not
accept them as semantically correct. Object identity, quantity, order,
evidence pages, bbox ownership, and routing were not changed or re-audited by
this Naming-only checkpoint.

## Deferred next experiment, not authorised by this checkpoint

Replace the contradictory single `cue` field with two fields:

- `cue_type`: a closed, machine-validatable category such as `sink` or
  `cooktop`;
- `cue_detail`: a short free-text explanation for audit display.

Validate `visual_group_id` against the locked object's real Registry View ids,
not merely for non-emptiness. Test that an object with `Kitchen` and valid
`cue_type` publishes its category, while an unsupported category or unrelated
View does not. This is a Naming-contract change and needs explicit approval
before implementation.
