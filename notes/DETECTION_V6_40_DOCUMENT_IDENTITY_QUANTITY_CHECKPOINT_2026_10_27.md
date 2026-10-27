# Detection V6.40 document identity and quantity checkpoint

Date: 2026-10-27

Status: owner-accepted code checkpoint for the ordinary route's quantity
publication, File Review quantity indication, and deterministic Document
Identity fallback. The three commits are published to `main`. Railway pickup
and healthcheck were not independently observed in this checkpoint.

Implementation commits:

- `06e54ee`, `fix(detection-v6.38): publish caption-bound quantities`
- `9686459`, `feat(detection-v6.39): infer semantic document identity`
- `f4312d9`, `fix(detection-v6.40): scope quantity review flags`

## Production witness

`300119_f2.pdf` selected `ordinary_haiku`, not Ada, Page23, or Assembly Set.
Its retained evidence includes the native title block and object-caption facts:

- `04 / ПОДДОН 5 ШТ`
- `03 / КОФЕ СТЕЙШН 1 ШТ`
- Project: `МЕБЕЛЬ / СТЕЙШН И ПОДДОНЫ`
- Client: `СТУДИЯ CALGEL`
- Partner: `ООО "АРХИПРОБА"`

The source facts are carried through existing OCR/Fusion evidence. No new
provider call, crop, prompt, model, or router decision was added.

## Accepted contract

### Quantity

After membership and object boundaries are locked, Detection promotes one
unambiguous positive quantity only when it occurs in a retained View's upper
caption band. Bounded aliases cover English, Russian, and Hebrew count forms.
Conflicting positive caption quantities preserve the safe quantity of one and
are recorded in the quantity audit.

Quantity one is the safe default when no explicit quantity exists. It is valid
for a unique built-in kitchen, large cabinet system, counter, or other integral
commercial object. An explicit quantity of one is also valid. A repeated or
non-one quantity must be grounded by an explicit source fact.

File Review's red `QTY` label now means exactly one thing: the same locked
object has conflicting explicit caption quantities. It never represents a
Registry metadata fallback or graph/package review condition. Therefore the
explicit Tray quantity five, the explicit Station quantity one, and safe
default-one built-in objects remain unflagged.

### Document Identity

Explicit Project, Partner, and Client labels retain priority. When they are
absent, deterministic title-block inference may publish:

- a design or architecture organisation as Partner;
- a named designer, when not credited as Author, as Partner;
- a non-design organisation immediately associated with an address as Client;
- an unlabelled document title as Project;
- an address as Project only if no title survives.

Each inferred identity has a cited semantic source label. Object Naming cannot
write Project, Partner, Client, Author, or Date fields.

## Verification

- `git diff --check` passed before commit.
- `py_compile agents/detection_agent.py` passed.
- Targeted quantity, registry transport, and File Review handoff tests passed:
  `39 passed`.
- The three-object transport regression proves that a default-one built-in
  object and an explicit-five object are not flagged, while a documented
  conflicting-caption object is flagged.
- The `300119_f2.pdf` evidence audit confirmed the two literal quantities and
  the Project, Client, Partner mapping above.

## Protected boundaries

- V6.37 Ada covered-membership remains protected and unchanged.
- Page23, Assembly Set, router selection, object boundaries, View bbox
  ownership, Evidence page membership, Naming, Preview selection, and
  Estimation handoff are unchanged.
- The generic Registry metadata and graph review diagnostics remain available
  in Detection raw usage. They no longer masquerade as quantity uncertainty in
  File Review.
- This checkpoint does not claim a complete quantity parser for arbitrary
  schedules, tables, or component-level notes outside the object's bounded
  caption band.

## Next safe work

Use a new real document with an intentionally conflicting caption quantity to
exercise the one remaining red-`QTY` condition. Do not expand the quantity
parser or alter the protected routes without a separate benchmark.
