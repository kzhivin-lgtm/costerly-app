# TODO

CHECKPOINT, V6.23 bounded Naming and Quantity review presentation:
`c990495`, deployed and audited as
`notes/DETECTION_V6_23_NAMING_AUDIT_CHECKPOINT_2026_10_26.md`. HSL returns to
11 OCR pages, $0.044 OCR cost and a 72.243-second initial cycle. V6.23 retains
the V6.22 Kitchen-oriented Naming pass, but its final names are not accepted:
the model correctly proposes `Kitchen` from sink/cooktop evidence, then the
contradictory `category_evidence.cue` validator rejects those rows and leaves
source codes in the UI. Do not change Naming, routing, identity, quantity,
order, bbox, evidence-page membership or View ownership at this checkpoint.

SUPERSEDED, V6.24 compact Kitchen Naming repair: the model complied with its
compact Kitchen cue tokens, but the runtime then rejected visual evidence whose
`visual_group_id` was blank. The object crop had a valid locked group id, but
the model never received it. Preserve the compact cue and 12-word basis rules.

CHECKPOINT, V6.25 bound visual Naming evidence: `a34497b`, deployed and
accepted at `notes/DETECTION_V6_25_HSL_CHECKPOINT_2026_10_26.md`. HSL run
`run_2dceafe62d3440668ca56b6b74101cc8` produced 9 objects, 11 OCR pages at
$0.044, a 69.777-second initial cycle, accepted Naming validation and 9/9
created previews. P11's three evidence regions are one locked object, with
`view-033` selected as its presentation source. The names are operationally
accepted but not a semantic-quality benchmark. Do not reopen Naming, router,
object identity, quantity, order, bbox, evidence-page membership or View
ownership without separate explicit approval.

CHECKPOINT, preliminary, V6.26 assembly-set compiler: retain the V6.12
pre-Sonnet category and V6.11 validated scope observation, but make a
confirmed `assembly_set_candidate` publish one locked commercial Object only
after Registry validation. The compiled Object has quantity one, uses cited
root pages as identity anchors, retains every Registry-owned Island, and
includes every uploaded physical page in its Estimation evidence so authored
notes, material schedules and detail sheets remain available. Shared order,
title-block, date, material, page count or numbering alone still cannot
trigger this compiler. If scope is ordinary, missing, or its roots are not
Registry-owned, preserve the original Registry packages unchanged.
The first V_Cabineter production run correctly selected `assembly_set` and
confirmed scope, but safely retained 14 Registry packages because Discovery's
provider Island IDs had not yet been normalized to Registry `view-NNN` IDs.
V6.26.1 maps those cited scope references before compilation. The same patch
also promotes a repeated explicit `Order`/`Заказ` code to a project identifier
only when no explicit Project field exists and it occurs on a strict document
majority. It must not infer client or partner facts.
V6.26.2 treats a rejected one-object Naming project fallback as a successful
Naming completion when Document Identity has concurrently published a stronger
project value. The fallback remains non-authoritative and its refusal is kept
in the Naming audit rather than surfaced as a false failure.
Owner accepted the preliminary checkpoint at
`notes/DETECTION_V6_26_ASSEMBLY_SET_CHECKPOINT_2026_10_26.md`: production run
`run_41fdb9846abb4c2b9e5cfc0d194b6fe6` on `V_Cabineter.pdf` selected
`assembly_set`, compiled one quantity-one Object, retained all six pages and
17 Views, and persisted `Order 1208`. V6.26.2 `c9cb521` is deployed to remove
the false red Naming failure caused by the concurrent Identity update, but
that narrow presentation repair has not yet had a production re-run. The
separate `V_Stair.pdf` run is a negative guard only, not a second assembly-set
benchmark: it correctly retained the ordinary route and one independent stair
railing Object.

DEFERRED, P1, assembly-set breadth validation: test a second genuinely
multi-sheet built-in/cabinet dossier after the V6.26.2 deploy, plus protected
Adda, HSL, and Page23 regressions. Do not expand the compiler rule from one
accepted V_Cabineter dossier or use object count alone as quality evidence.
`V_Stair.pdf` cost is not comparable to Cabineter: the former selected
`ada_sparse_multi_object` and Sonnet Detection, while Cabineter selected
`assembly_set` and Haiku. The latter's pre-V6.26.2 failed Naming event did not
record model tokens/cost, so `TC1 $0.105` is incomplete rather than a final
ten-cent total. ACTIVE, P0, V6.27 scope-scout experiment: retain the Ada guard
until a separate short Haiku observation classifies only its current candidates
as `single_assembly_candidate`, `multi_object_risk`, or `uncertain`. Only the
first result may use the existing Haiku Assembly Set Registry and compiler;
the other two retain Sonnet Ada. The scope scout cannot create Islands, merge
objects, or use shared title/order metadata as sufficient proof. Its cost must
be stored as a separate Detection usage event. V_Stair passed the local shadow
gate as `single_assembly_candidate` ($0.013431, 28.873 s). Adda's local scout
result was unavailable after two environment-level attempts, so production
Adda is the unresolved gate. The experiment's production acceptance requires
Stair to compile one all-page Assembly Set and Adda to stay on Sonnet with its
accepted two-object boundary.

CHECKPOINT, V6.27 optional-scope validation: a live RFQ failed with
`V6.11 document scope witness references an unknown group`. The V6.11 scope
sidecar may authorize assembly compilation, but it does not own Discovery
Islands or ordinary Registry packages. Reject an invalid scope sidecar,
record the exact validation error, and continue with the unchanged Registry
result. Do not delete the unknown reference, rewrite its evidence, or compile
an assembly without a fully valid scope. Local regression must prove the
unknown-group case returns no validated scope and retains an auditable error;
production run `run_62392d84938242cfa7d83b6060e7ce0e` proved that the invalid
sidecar is rejected while the ordinary Registry retains one quantity-one Object
with all five pages and seven Views. Protected at `e9e8548` and tag
`detection-v6.27-invalid-scope-recovery-production-2026-10-26`.

ACTIVE CANDIDATE, P0, V6.28 bounded witness and Identity ownership: retain up
to eight existing group IDs in one scope witness rather than randomly dropping
valid evidence. Keep four roots, four witnesses, and the 180-character bound.
Split group-limit diagnostics from unknown IDs. Promote an explicit identical
`Title` to Project only when it repeats on a strict majority of OCR pages, with
explicit `Project` still taking precedence. Naming publishes Object names only
and must never write Project, Partner, Client, Author, or Date. Protect V6.27
failure recovery, Registry boundaries, quantity, View ownership, Evidence, and
all accepted Naming behavior.
Local verification: 129 relevant Detection, Identity, Naming, and evidence tests
pass. A read-only replay of production run
`run_62392d84938242cfa7d83b6060e7ce0e` returns grounded Project `Офис` from
page 1 and validates the original witness counts `4, 3, 5, 3` with no scope
error. Fresh production acceptance remains pending.
The full repository suite reports 1445 passed and 20 unrelated existing
Estimation, material-policy, and UI-contract failures; none touches the V6.28
files or protected Detection/Identity/Naming paths. Those failures are not part
of this candidate and were not modified.

RESOLVED, V6.22 grounded title facts and Kitchen Naming: retain the V6.21
deferred Naming lifecycle and locked Detection object contract. Build optional
`page_title_fields` during OCR/Fusion from explicit title-field label-to-value
evidence, including full-page Mistral Markdown only as explicitly marked
single-source fallback. Preserve `representation_kind` in the private
Registry-owned sidecar so deterministic preview and Naming crop selection can
prefer elevation over section. Extend the Naming response with object-local
`category_evidence`; Kitchen can cite a sink, faucet/mixer/tap, or kitchen
appliance, while strong categories such as Kitchen and Stair railing must not
publish without an object-local literal or visual cue. Do not change router,
object identity, quantity, order, bbox, evidence-page membership or View
ownership. First gate: HSL audit of title facts, selected source crops and
grounded category evidence. Then run Page23 and Ada regressions.

RESOLVED, V6.21 object-bound Naming evidence and presentation preview: retain
the V6.20 deferred Naming lifecycle and neutral File Review publication, but
make one deterministic Registry-owned front/elevation View available in two
strictly separate roles. It becomes `presentation_preview_bbox` for File
Review only, and its source crop becomes bounded visual context for Naming.
Full annotated pages and local OCR snippets remain in Naming. Do not pass the
UI preview field to Naming or Estimation, and do not change object identity,
quantity, order, evidence-page membership, or View ownership. When a repeated
title-block identifier family is a strict document majority, omit isolated
minority-family codes from the private Naming transport, so a project/file
code cannot be published as an object index. Acceptance: HSL produces stored
front/elevation previews, no `FTC201.06` prefix, and a terminal Naming audit
whose category decisions can cite object-bound visual/OCR evidence. Reassess
the P11 object split separately from Naming: it is a locked Detection-boundary
question, not a name rewrite.

RESOLVED, V6.20 Naming publication and cost lifecycle: preserve the V6.14
Detection checkpoint while repairing the V6.19 deferred Naming worker call,
show `TC1` for completed OCR plus Detection and `TC2` only after terminal
Naming, and keep File Review labels as neutral `Object NN` until one Naming
publication atomically applies the source index with the category name.
Acceptance: HSL performs one terminal Naming call, Naming cost/time appear in
the ledger and File Review, and the locked Detection object identity, count,
order, and evidence remain unchanged. File Review polling must not remount
visible metadata or object cards while no deferred work changes state.

CHECKPOINT, experimental, Detection V5.7.1 is recorded in
`notes/DETECTION_V5_7_1_EXPERIMENTAL_CHECKPOINT_2026_10_23.md`. It is not
accepted or deployed. The measured membership-edge path passes Page23 and
Adda in one run, but HSL regresses to 29 Object Islands and 10 packages.

SUPERSEDED EXPERIMENT, V5.7.1 MVP boundary experiment: start from protected
V5.6.1 checkpoint `5de4cf4`. Registry owns one full-page, non-overlapping
membership proposal for multi-View physical items. Runtime validates typed
facts, exclusive ownership and exact proof trees, but Dimension Similarity and
OCR-locality cannot overturn a valid visual membership proposal. First gate is
Page23 membership, then Adda, HSL and Metal. No extra model call, router,
Sonnet path or file-specific rule.

SUPERSEDED EXPERIMENT, V5.7.1 preserved both Registry evidence paths: direct
`semantic_facts` and membership-edge facts. V5.6 silently ignored direct
facts, so a valid typed criterion could not reach the supporting graph. Keep
the same validators and audit both paths separately.

RESOLVED, V5.7.1 local benchmark invocation: long runner commands return a
PTY session after 30 seconds and must be drained until completion. The prior
missing HSL/Metal reports were orchestration timeouts, not Detection failures.

SUPERSEDED EXPERIMENT, HSL V5.7.1 regression: a full run now completes, but produces 29
object-evidence Islands and 10 packages versus the protected 32/9 benchmark.
The visible losses are page 3 (2 rather than 3 raw Islands) and page 11 (four
raw Islands but only one object-evidence Island). Keep the V5.6.1 Island and
classification contract while isolating the membership-output change. Diagnose
Island recall and classification before considering V5.7.1 for acceptance.

SUPERSEDED EXPERIMENT, V5.7.2 isolates the V5.6.1 Registry prompt and JSON contract,
then deterministically adapts each accepted `object_hypothesis` into N-1
membership edges. HSL `v572-hsl-03` restored 32 Object Islands, but returned
10 packages. P04 was split into two complete hypotheses, while V5.6 merged
their components later through the same-page, 100-score Dimension
batch-confirmation edge `view-004` to `view-005`. The owner later clarified
that P04 may legitimately contain one to three products, so this historical
count is not evidence for either joining or splitting it. Do not use P04's
package count to justify a deterministic bridge or any other membership rule.

SUPERSEDED EXPERIMENT, V5.7.2 three-file regression evidence: Adda `v572-adda-01` passes
at 9 Object Islands and 2 packages. Page23 `v572-page23-01` returns 4/4: the
Registry emitted four forbidden singleton hypotheses, all correctly rejected,
so it created no membership edges. Metal `v572-metal-01` returns 51/11, not a
quality pass: it combines distinct marks OM-2 and OM-3 on P03, OM-1 and MP-1
on P06, and OG-1, OG-2 and OG-3 on P11 into individual hypotheses. Do not run
more regression documents or promote V5.7.2. Decide a membership contract that
can retain complete grouping without admitting singletons or merging explicitly
distinct author marks.

SUPERSEDED EXPERIMENT, V5.7.3 one-call visual-inventory and typed-pair experiment:
preserve V5.6.1 Island/classification rules, eliminate Registry package and
membership-tree output, and compile packages only from validated positive
pair facts plus Dimension Fingerprint/Weighted Similarity. Q is bounded by
concentric proximity: scored same-page pairs, one same-page fallback for an
unanchored proto-region, and only >=85 cross-page anchors. Registry output
must record full-page/crop image counts and bytes, every Registry text block's
character count, Q before/after counts, input/output tokens and their separate
costs. Do not change crop selection in this experiment, so a quality change
has one attributable cause. First benchmark Page23, then HSL, Adda, and a
membership-level Metal review. Target is a quality gate before a separate
crop/input-context cost experiment.

BLOCKED EXPERIMENT, V5.7.3 Page23 quality gate failed twice. `v573-page23-01`
returned 4 Object Islands but 2 packages because a single false
`direct_shared_structure` joined the independent shelving and door systems.
After a narrowly worded shared-member guard, `v573-page23-02` regressed to 5
Object Islands and 2 packages, with three unsupported single semantic merges.
The prompt-only route is rejected after two attempts. Do not benchmark HSL,
Adda or Metal on this state. Next diagnostic is deterministic semantic-proof
strictness: distinguish a real structural/topological identity proof from a
shared material, frame type, hardware or page-wide dimension before allowing
one typed fact to create a merge.

SUPERSEDED EXPERIMENT, V5.7.4 MVP recovery restored the exact V5.6.1 membership-first
Registry output contract, complete non-overlapping `object_hypotheses`, and
V5.6 deterministic package assembly. Retain Dimension Fingerprint and
Weighted Similarity as supporting/bridging evidence, not a replacement for
the Registry's full-page visual grouping. Retain V5.7.3 diagnostic telemetry
only: full-page and crop counts/bytes, each prompt-context character count,
Q counts, Anthropic input/output tokens, separate calculated costs and
duration. Do not add another model call, a router, Sonnet, crop changes, or
unproven semantic wording. First run Page23, then HSL, Adda and membership
review of Metal. Do not accept a single successful Page23 run as stability.

BLOCKED QUALITY GATE, V5.7.4 Page23 `v574-page23-02` and `-03` produced the
same invalid raw Registry response: five Object Islands and five forbidden
singleton hypotheses, all correctly rejected by runtime into five standalone
packages. Claude cost was `$0.018720` per completed run: 8,925 input and
1,959 output tokens; one full page plus three static crops carried 402,136
JPEG bytes, and text context was 10,821 characters. Historical successful
V5.6 traces returned hypothesis sizes `[1, 1, 2]`; current runs return
`[1, 1, 1, 1, 1]`. Do not spend on the remaining pack until the Registry
prompt explicitly reconciles a physically continuous drawing and alternate
projections of one fixture before outputting its Island inventory.

BLOCKED EXPERIMENT, V5.7.5 one-call visual-reconciliation experiment preserved the
V5.6.1 membership-first contract and V5.7.4 telemetry exactly. Before JSON,
Registry must reconcile a physically continuous depiction as one Island,
compare alternate projections, and remove singleton `object_hypotheses`.
No schema, Dimension, crop, package-runtime, router, Sonnet, or extra-call
change. Page23 `v575-page23-01` passes the narrow gate at four Object Islands
and three packages. The pack rejects it: HSL `v575-hsl-01` retains only 30
Object Islands and 10 packages, with P11 classified down to one Object Island;
Adda `v575-adda-01` retains nine Islands but merges all four sheets into one
package instead of the protected two; Metal `v575-metal-01` returns 48 Object
Islands and 10 packages, which is observational only because aggregate Metal
package count is not an acceptance signal. Do not promote or extend this
prompt direction. The reconciliation wording is too broad across sheets and
must not be tuned again without a new causal diagnostic.

BLOCKED EXPERIMENT, P0, V5.8.0 two-pass Registry: retain Fusion, candidate
Regions, View Evidence Packages, Dimension Fingerprints, Weighted Similarity,
the V5.6 deterministic graph and standalone fallback. Haiku call one is
Discovery only: full pages plus fixed enlarged regions, Islands, bboxes,
classification and Candidate Region recall, with no OCR inventory, Q,
object hypotheses or semantic facts. Call two is Membership only: fixed
Object View crops, concise View-local facts and document-context descriptions;
it cannot create, remove or classify Islands and returns only multi-View
hypotheses. Page-wide OCR spans are excluded from a View-local membership
handoff. Persist each call's token, cost, duration, prompt/context characters,
image count and image bytes, as well as aggregate cost. `v580-page23-03` is
the first valid end-to-end trace after the Registry crop sources were wired
through final validation: `$0.016990`, Registry `21.768s`, total `28.719s`.
It rejects the quality gate despite returning three packages. Discovery emitted
five Object Islands. Membership incorrectly merged the door elevations with an
unrelated angled panel, while leaving the physically continuous shelf-and-panel
depiction separate. Do not spend on Adda or HSL, tune generic semantic wording,
or promote V5.8 from this trace. The next decision is whether Membership gets
a bounded full-page visual context in addition to crops, or whether Discovery
must return explicit continuous-drawing component ownership. No Router or
Sonnet.

BLOCKED EXPERIMENT, P0, V5.8.1 Membership page-context experiment: retain the V5.8
two-call responsibilities and every fixed Island/classification boundary. Add
one JPEG page context, longest side `1024`, only for pages containing fixed
Object Views, before the existing View crops in the Membership call. It may
identify continuity and alternate View arrangement, but cannot create, remove,
merge or reclassify Islands. First gate is Page23 exact grouping: shelf with
its continuous panel, doors alone, console projections together. Record the
incremental Membership image bytes, tokens, time and cost before any wider
benchmark. `v581-page23-01` rejects the exact grouping gate: it repeated the
false doors-plus-angled-panel merge and split the two console projections after
the generic direct-shared-structure guard rejected one of their two facts.
Compared with `v580-page23-03`, page context added 81,365 image bytes, 1,047
Membership input tokens and `$0.001082`, but did not correct the false link.
The crop-only-context hypothesis is rejected. Do not run Adda or HSL, tune
semantic wording, or promote this direction. No Router, Sonnet or extra call.

CHECKPOINT, experimental, V5.10.3 two-call Registry: retain Fusion and the
deterministic graph, but separate visual discovery from commercial membership.
Haiku call one receives the rendered pages, Fusion and Candidate Regions, and
returns only immutable Islands, classifications and candidate exceptions.
Haiku call two receives the fixed inventory, page overlays, View crops and
local evidence, then returns only non-singleton multi-View hypotheses. Runtime
alone validates citation IDs and typed positive facts, computes Dimension
Similarity, compiles the graph and creates packages. Both calls use Haiku at
temperature zero. Exact display wrappers such as `[SF00123]` are canonicalised
only when `SF00123` is a known source ID, with an audit row. This checkpoint is
not accepted or deployed. Protected evidence and limits are recorded in
`notes/DETECTION_V5_10_3_TWO_CALL_EXPERIMENTAL_CHECKPOINT_2026_10_23.md`.

VERIFIED LOCALLY, pending checkpoint, P1, V5.10.6 P02 generic floor-plan classification.
The V5.10.3 HSL run retained all protected P03-P11 Island inventory but emitted
P02 as `object_evidence` because it mislabeled `representation_kind` as
`object_evidence`, bypassing the generic-plan safeguard. Repair this upstream
classification-contract breach without changing Island membership, graph,
dimension scoring or P04 package policy. Re-run HSL first, then Page23 before
any broader regression pack.

CHECKPOINT, experimental, V5.10.12 evidence, context and same-page Dimension
repair. This is a protected local evaluation baseline, not accepted or deployed.
V5.10.5 preserved P09.V3 outer dimensions but the final Dimension Graph passed
`allowed_pairs=Q`, which disabled same-page all-to-all after Registry.
Candidate Regions omitted the lower P03 and P09 sections, so their final
Islands received no Dimension pair, semantic fact or graph edge. V5.10.6
scores every final same-page object-Island pair and uses Candidate Q only for
bounded cross-page revalidation. Keep the 25 threshold and cross-page >=85
early stop unchanged. It also demotes a whole architectural floor plan to
`document_context` from its concrete description when Registry incorrectly
emits `representation_kind=object_evidence`. V5.10.7 required verbose per-page
reasoning, which pushed one HSL proposal to its 8,192-token cap. V5.10.8 keeps
the same validated all-pages/all-Islands invariant in a compact page-to-Island
ID map. It fixes the silent P09 omission without raising a token budget or
adding a call. V5.10.8 then restored all P09 Islands, but P09.V3 had no
Dimension edge because its Registry envelope ended 66 pixels above the printed
total `407`; the matching `406` was retained by P09.V2. V5.10.9 tried a Review
completeness instruction and explicitly still classified P09.V3 standalone, so
that prompt-only change was discarded. V5.10.10 attaches an otherwise-unowned
numeric fact of at least 20 in a bounded 80-180 px evidence halo only when
exactly one final Island contains it. This excludes title-block revision rows
such as 1..10 and cannot duplicate or steal a fact across overlapping halos.
V5.10.12 fixes the remaining earlier recall failure: where Mistral exposes no
graphic region on a page, Fusion derives broad, disconnected text/dimension
clusters as Candidate Regions. They only require Registry to inspect those
areas, retain the full-page rule, and never decide Islands or object identity.
Graphic-region pages retain their existing Candidate Region behavior. The
candidate log records the recall basis, including `fusion_text_cluster`.
Local HSL `v51012-hsl-01` passed the primary gate: P02 is Document Context,
P03.V1-V3 are one package, P09.V1-V3 are one package, and P09 has five
accounted recall regions, including a non-Island revision table. It produced
32 Islands and 10 packages in 124.481 seconds at $0.208045. This is an
uncheckpointed local result. Page 23 `v51012-page23-01` confirms this fallback
did not run on ordinary Mistral graphic-region pages, but exposed an independent
semantic-validation defect: generic material/frame language incorrectly merged
door and console Views. It produced five object Islands but the false packages
`P01.V1+V2` and `P01.V3+V4+V5`. Do not checkpoint or deploy. Next isolated
audit corrected the causal label for the zero Dimension pairs. This is not a
Fusion-to-final-Island ownership loss. `page-23.pdf` has only nine native text
spans, all headers, footer, page number, or two notes, and no authored drawing
dimensions. The current one-page Mistral response returns one `image` block
covering the drawing, no interior text blocks, no image annotation, and only
image Markdown. Fusion therefore never receives dimension literals such as
4130, 2345, 2695, 1760 or 3610 with usable coordinates. Treat OCR recall and
locality as a separate early evidence repair. Independently, Registry sees the
full page in both calls but split the physically continuous left shelving and
its diagonal extension into P01.V1 and P01.V2. Repair that Island-segmentation
breach before using semantic facts to mask it. Only then tighten
`matching_topology` and `direct_shared_structure` around pair-specific topology
or an actual shared physical structure. Rerun Page 23 before the remaining
benchmark pack.
Mistral native coordinate blocks remain the confirmed stable OCR path; do not
restore the rejected per-item bbox response schema.

REJECTED LOCAL EXPERIMENT, V5.10.13 Page23 OCR crop and Island-water prompt:
the isolated 200-dpi crop of the complete left shelving unit, including visible
dimensions 2695, 1760, 1660, 630 and 510, still returned one Mistral image
block, image Markdown and zero text or dimension facts. Enlarging the image is
therefore not an OCR recovery path for this provider response. The Proposal
prompt then required a 10-Fusion-pixel water gap and a continuity recheck before
creating Islands. Page23 `v51013-water-01` still returned five Object Islands:
it called the shelf `VG-P1-001` and its visibly attached diagonal extension
`VG-P1-002` independent components, then Review re-merged them into one object.
It retained the correct three final packages but did not repair the Island
boundary. Revert this prompt-only variation. Do not try another wording-only
variant. Any next repair must give an existing stage an explicit, bounded
authority to invalidate a false split, or add a deterministic image-continuity
signal that distinguishes physical body strokes from annotations.

REJECTED LOCAL EXPERIMENT, V5.11 visual-only alternatives: direct Haiku
object discovery, high-resolution retry, isolated visual membership review and
bounded nearest-neighbour visual pairs all failed the Page23 exact grouping
gate. The pair route was invalidated earlier by incorrect View envelopes, which
omitted the required console pair and introduced false neighbours. V5.11 was
never wired into the active Detection path. Do not create a page router, use
Sonnet, or tune this prompt family further.

RESEARCH RESULT, legacy V3/V4 Page23: the historical stable 3-object outcome
does not prove a universal mechanism. Both active legacy prompts contain a
literal example of the Page23 composition, demanding three objects and the
two-view console merge. The reusable observation is narrower: temperature-zero
Haiku made one full-page visual inventory before any bbox candidate constrained
it. It correctly represented the shelf as one complete assembly view, doors as
one track system and the console as two views. It then applied exclusive
ownership. Do not restore the old direct Registry, its Page23-shaped example,
or unvalidated free-text boundary reasoning. Any successor needs a separately
approved full-page-first Island authority while keeping Fusion, Dimensions and
runtime validation.

PENDING, P0, USER DIRECTION, degraded-source visual route: build a separate
Haiku-only Detection path for drawing packages whose Fusion contains no usable
spatial source evidence on every substantive page. This is an input-capability
decision, never a filename, object-count, Page23, document-type or Sonnet
route. The deterministic gate must distinguish authored, page-local MyPDF or
OCR text/dimension/graphic facts from page headers, footers and a provider's
whole-page image placeholder. On a routed file, bypass Candidate Q but retain
visual-source Dimension Fingerprints, typed semantic facts, full rendered
pages, source-quality audit, role classification, exclusive ownership,
Detection Validation, File Review and later Naming. The alternative Haiku
route first builds a full-page visual inventory before any rectangular candidate
boundary, then resolves commercial membership from that inventory. Mixed-evidence
files remain on the ordinary V5 route until a separate mixed-page contract is
approved. Acceptance must cover varied zero-source files, not a Page23 rule.

PENDING, P1, USER DIRECTION, mixed-evidence documents: define a separate
per-page capability and cross-page ownership contract. A single source-degraded
page must not discard good Fusion facts from other pages, and a visual-only
page must still be eligible to join an object evidenced on a structured page.
Do not begin this work during the V5.12 document-level visual-only experiment.

FAILED QUALITY GATE, V5.12 source-degraded visual route, Page23
`v512-page23-02`: the document-level capability gate correctly excluded a
footer address (`100`, `472`) and two adjacent OCR rows of one cable-hole note;
the document has zero usable coordinate evidence and entered the visual-only
route. Two Haiku calls returned five Object Islands and five singleton packages
instead of the required four Islands and three objects. Discovery split the
physically continuous shelving assembly from its diagonal extension, then
Membership did not create any false merge. This isolates the current failure to
full-page visual continuity in Discovery, not Fusion, Dimension Fingerprint,
or Membership validation. The experiment cost `$0.019223` and took 36.470s
wall time, including 7.035s Mistral OCR. Do not wire or deploy V5.12 from this
run. The separate mixed-evidence P1 contract remains deferred.

PENDING EXPERIMENT, P1, USER DIRECTION, ordinary V5 static-crop ablation:
Proposal currently receives every full page plus three fixed static crops
(`upper_left`, `upper_right`, `lower`). The static three-zone topology has no
established advantage and can present one continuous physical depiction as
separate partial images. Remove only these pre-Discovery crops. Retain Review
View crops, because they are produced only after the Island inventory is fixed
and therefore cannot create an Island split. Keep full pages, Fusion, Candidate
Regions, Dimensions, semantic facts and deterministic graph policy. Compare
HSL Island inventory and Page23 commercial boundaries, as well as input bytes,
tokens, cost and duration, before changing the ordinary default.

PENDING DIAGNOSTIC, P0, V5.12.1 source-degraded semantic proof: Page23
`v5121-page23-02` recovered the required four Islands without any crop, but
incorrectly merged the shelving assembly with the TV console. The only causal
semantic fact was `direct_shared_structure` based on a generic claim of the
same metal-frame "principle" or "construction methodology". Define and test a
physical-continuity witness for this fact before widening any validator: either
one View visibly contains both otherwise separate parts as one attached
assembly, or a partial View is visibly continuous with a complete View of that
same assembly. Shared material, profile, frame type, construction method or
similar dimensions are never a witness. Page23 is the first discriminator.

FAILED QUALITY GATE, V5.12.2 source-degraded semantic proof, Page23
`v5122-page23-01`: the new `direct_shared_structure` witness correctly
rejected the original generic metal-frame claim, but Review re-labelled the
same generic resemblance as `matching_topology` and `unique_geometry`. Runtime
therefore accepted six non-specific facts and merged all four Views into one
object, rather than the required three. This rules out a type-specific wording
or blacklist repair. The next approved repair must require a criterion-specific
structured witness for every semantic fact: literal author relation, paired
axis/value transform, recurring ordered topology, named distinctive geometry,
or a physical-structure witness. It must reject generic rectangles, frames,
materials, construction principles and broad visual resemblance regardless of
which evidence type the provider selects. Do not repeat Page23 until that
contract is implemented and unit-tested.

ACTIVE EXPERIMENT, P0, V5.12.5 source-degraded nested-Island resolution:
the visual-only route no longer fabricates a deterministic Dimension Fingerprint
from incomplete model transcription. Discovery locks Islands only. Membership
gets full-page overlays plus post-Island View crops and returns the sixth typed
criterion `visual_dimension_similarity`, citing both Views and concrete visible
readings. It also emits only explicit, grounded dimension conflicts, never an
absent or unknown state. V5.12.4 requires numeric readings separately from both
endpoints of a conflict and directs Membership to inspect every allowed pair for
positive proof before returning any conflicts. V5.12.5 additionally permits a
grounded `nested_duplicate_island` decision: a visually contained fragment with
no independent drawing boundary is removed before graph construction, while
ordinary overlapping boxes remain distinct. A conflict blocks that pair; a
similarity alone remains supporting and must combine with another concrete
criterion. The special route does not use batch confirmation. First gate is
Page23: four Islands and exactly three objects, with the two console projections
merged and no shelf/console merge. This is uncheckpointed and must not affect
ordinary V5.

RESULT, V5.12.4 Page23 `v5124-page23-04`: the conflict repair worked narrowly.
Five conflicts with concrete numeric readings from both endpoint Views were
accepted; two legacy-like conflicts whose second View had only material labels
were rejected. Discovery still returned five rather than four Islands, and
Membership returned no positive fact or merge edge, so all five Views remained
singletons. It also omitted the three potentially relevant console pairs from
the returned facts and conflicts. The next isolated diagnostic is an exhaustive
pair-review receipt, separate from the graph, to prove that every allowed pair
was inspected before changing any merge threshold or Island rule. The run cost
`$0.022056` and took `41.454s` wall time (`15.213s` Mistral, `25.768s` model).

REJECTED, V5.12.5 nested-Island rule, Page23 `v5125-page23-01`: Discovery
still returned five groups and Membership returned neither a nested-duplicate
decision nor semantic facts. The apparent duplicate was not actually contained
by the immutable core boxes in this run: its overlap with the larger candidate
was about `68%`, and it extended materially above it. Do not lower the `85%`
containment guard. The supported diagnosis is a fragmented continuous drawing,
not a nested duplicate. The next distinct proposal, if approved, is an Island
reconciliation relation for same-page fragments whose visual contours visibly
continue into one another. It is a segmentation repair before the object graph,
not a semantic object merge. V5.12.5 cost `$0.016119` and took `29.157s` wall
time (`3.867s` Mistral, `24.728s` model).

REJECTED EXPERIMENT, P0, V5.13.2 source-degraded representation-map roles:
Discovery emitted six representations on Page23 and Review assigned every one
an explicit role, but still created a false shelving-to-door relation and split
the two console projections. The isolated route preserved full pages and
disabled Discovery-coordinate crops because its rendered-frame boxes are not
authoritative. The failure proves that a role taxonomy followed by pairwise
semantic facts cannot replace global object partitioning. Do not tune its pair
prompt further.

REJECTED EXPERIMENT, P0, V5.14 source-degraded full-page Registry partition:
Discovery remained advisory and a second full-page Haiku call owned all roles
and one exclusive partition. Its first response correctly labelled a component
but illegally included it in a partition, which runtime rejected. Its second
response technically passed but falsely merged shelving with doors and left the
two console projections separate. The V4-style partition validator, role
coverage, exclusive ownership and graph materialization worked as intended;
the visual conclusion did not. Cost was `$0.015468`, total wall time `24.807s`.
Do not promote or continue prompt-wording variants of this two-call route.

REJECTED EXPERIMENT, P0, V5.15 source-degraded one-shot full-page Registry:
To remove the two-call map handoff, one Haiku full-page decision produced the
representation map, roles and exclusive partition together. Page23
`v515-page23-01` correctly made the continuous shelf-and-panel one assembly,
kept doors separate, and classified a detail and footer out of ownership, but
still separated the two alternate console projections. It returned four
objects, not the required three, at `$0.013936` and `32.676s` wall time. This
rules out the intermediate map handoff as the sole cause. The historical V4
Page23 result is not an acceptance target because its prompt contained a
literal Page23-shaped example. Do not copy that example or promote V5.15.
Any next source-degraded mechanism needs a document-independent way to ground
alternate-projection identity beyond free visual prose.

REJECTED EXPERIMENT, P0, V5.16 source-degraded V5.6.1 proposal consensus:
two independent 200-dpi full-page Haiku calls, with no pre-Discovery crops,
each returned the same six Object Islands and only forbidden singleton
hypotheses on Page23. The deterministic consensus correctly retained no merge
edge, leaving six standalone packages rather than four Islands and three
objects. Both calls had equal 4,678 input and 2,045 output tokens, and their
normalized maps and decisions were identical, so an identical second proposal
does not create independent evidence. The route gate, no-crop input, Island
matching and consensus materialization behaved as specified, but the quality
gate failed. The retained report cost was `$0.029806`, with latest recorded
wall time `50.068s`. An earlier command reused the same label and may have
overwritten its report, so session-level spend must not be inferred from that
single artifact. Do not tune this prompt or repeat the same consensus mechanism. The remaining diagnostic is to
compare the exact historical V5.6 rendered image transport and present visual
input with no model-contract changes, since V5.6 results cannot be replayed by
its text contract alone.

ACTIVE EXPERIMENT, P0, V5.17 source-degraded post-Discovery view crops:
retain V5.14's two distinct roles and its global exclusive partition contract.
The only changed provider input is that the second call receives the same
authoritative full rendered pages plus one padded crop for every first-call
candidate view. No static grid crop, prompt criterion, role rule, graph rule,
ordinary V5 path, or source-degraded router gate changes. Crops are created
only after Discovery and are supplemental detail, never a boundary authority.
Local structural verification created five valid crops from the historical
Page23 Discovery map, alongside the original 200-dpi full page; 45 focused
tests and `git diff --check` pass. The live provider gate was not executed:
this execution environment exposes project keys without DNS and exposes DNS
without local secrets, so neither Mistral nor Haiku was called. V5.18
supersedes this experiment's crop input.

ACTIVE EXPERIMENT, P0, V5.18 source-degraded full-page partition repair:
remove V5.17's post-Discovery crops entirely. In the final full-page Registry
response, discard only a partition whose members are all known Views already
classified as `component_detail`; persist that deterministic repair in the
decision audit. Unknown IDs, mixed detail and assembly partitions, duplicate
or missing assembly ownership, and invalid visual bases remain hard validation
errors. Ordinary V5 is unchanged. Local structural verification: 57 focused
tests and `git diff --check` pass. Provider-quality outcome remains pending,
and this repair must not be represented as a Page23 object-boundary fix.

ACTIVE RELEASE, P0, V5.19 Detection decision ledger: V5.18's source-degraded
route returned an internal usage dictionary rather than a database event. Its
missing required ledger fields caused the asynchronous batch write to lose
route choice, Islands, roles, partitions and Registry reasoning, while File
Review still showed final objects. Build a DB-ready, timestamped Detection
event for both success and validation failure. Persist it synchronously before
File Review, one event at a time; abort rather than expose an unauditable
Detection decision if that write fails. Continue storing OCR and timing
diagnostics asynchronously. Ordinary V5 decision logic is unchanged.

REJECTED EXPERIMENT, P0, V5.20 source-degraded continuity consolidation:
retain V5.19's two full-page Haiku calls and add an explicit same-page
`continuity_groups` response before roles. A deterministic core-bbox overlap
cue correctly surfaced the Page23 shelving and angled-panel pair as the only
candidate. The full-page Registry nevertheless returned an empty continuity
list, retained the panel as `component_detail`, falsely merged shelving with
doors, and left the console projections separate. The runtime consolidation
and audit behaved as specified, but the provider did not supply the required
physical-contour observation. Live visual-only Registry cost `$0.015511` for
6,881 input and 1,726 output tokens in 21.694 seconds. Reverted to V5.19.
Do not retry this prompt/schema mechanism. The next diagnostic must change the
visual evidence presented for connected-contour recognition, without restoring
static crops or treating bbox overlap as a merge decision.

PROTECTED EXPERIMENTAL CHECKPOINT, P0, V5.21 source-degraded mandatory
boundary ledger: user explicitly approved a narrower replacement after V5.20's
audit showed that the model could leave a continuity candidate unanswered. The
route keeps two full-page Haiku calls and no crops. For every same-page
core-bbox-overlap pair, Registry must return one physical-boundary decision:
`physically_continuous` plus concrete joined geometry, or
`physically_separate` plus `visible_background_gap`,
`separate_closed_contour`, or `independent_projection`. The code accepts no
silent split, unions only attested continuous pairs before roles, and writes
both the full boundary ledger and resulting consolidation audit. This does not
make bbox overlap a merge decision and does not alter ordinary V5.

Production Page23 run `run_caed454c5f6b49479d300f0b532c85c4` executed the
V5.21 prompt and supplied the required V1/V3 answer. It incorrectly asserted
`physically_separate / independent_projection` from different dimensions and
an alleged lack of common geometry, without identifying a visible separator.
The run nevertheless produced packages V1, V2 and V4+V5. This is an accepted
continuation checkpoint, not segmentation-quality acceptance. Preserve the
boundary ledger and do not add more prompt/schema variations automatically;
the next approved diagnostic requires independent visual evidence of physical
continuity. Details: `notes/DETECTION_V5_21_SOURCE_DEGRADED_BOUNDARY_LEDGER_CHECKPOINT_2026_10_24.md`.

SUPERSEDED EXPERIMENT, P0, V5.22 source-degraded local contour witness: retain
V5.21's two full-page Haiku calls and no pre-Discovery crop. Replace its
overlap-only boundary queue with a bounded local same-page core-neighbour
queue. For every selected pair, Registry must supply a coordinate-bearing
physical witness inside a deterministic local inspection corridor. A continuous
claim names and locates the visible construction joint. A separate claim names
and locates a visible background gap or separate closed contour.
`independent_projection`, dimensions, material, annotations and differing
perspective are prohibited as local-boundary evidence. Deterministic code
records whether the witness agrees with the rendered pixels and unions only
pixel-consistent continuous claims before roles. This is a source-degraded
segmentation experiment only, not an ordinary V5/Fusion/Dimension change.
First gate: Page23 must account for every local contour pair and either join
the shelving frame to its attached angled panel with a witness or expose a
failed witness in the audit. Record candidate count, witness coordinates,
pixel audit, roles, partitions, time and cost before broader testing.

SUPERSEDED EXPERIMENT, P0, V5.23 source-degraded role evidence: retain V5.22's
two full-page calls, no pre-Discovery crop and local contour audit. Change
only the final role contract. Every `assembly_view` must assert a complete
fabricated system, which can be a complete 2D elevation rather than a 3D
carcass. Every `component_detail` must either cite a same-page assembly parent
or state an explicit isolated-fragment basis. A full track/frame plus its
complete leaf, panel, bay or door sequence and system dimensions cannot be
discarded as a detail solely because it is technical or 2D. First gate:
Page23 must preserve a single shelving island, retain the door elevation as
an assembly, retain panel-only detail as supporting evidence, and merge the
two console projections only through a valid object basis. This is not a
Dimension Engine, ordinary V5, segmentation, crop or naming change.

SUPERSEDED EXPERIMENT, P0, V5.24 source-degraded overlap guard: retain V5.23's
role-evidence contract and V5.22's local contour witness. Make every
same-page overlapping core pair mandatory for contour review before applying
the bounded nearest-neighbour queue. This records the proven Page23 shelf
failure where an attached angled panel overlapped the shelving core and V5.21
accepted `independent_projection` without a physical separator. The overlap
guard never merges views itself. Registry must still return a local physical
witness and deterministic code must still accept only pixel-consistent
continuity. Regression fixture: the historical V5.21 Page23 V1/V3 boxes must
always enter the contour queue. This changes neither role semantics, object
merge, crops, Dimension Engine nor ordinary V5.

SUPERSEDED EXPERIMENT, P0, V5.25 V5.21 plus physical overlap witness: revert the
source-degraded route's role contract and non-overlap neighbour queue to the
V5.21 baseline. Retain only the mechanism that addresses the historical
Page23 shelf split: every overlapping same-page core pair must provide a
coordinate-bearing physical witness; `independent_projection` cannot explain
separation; deterministic code accepts continuity only after its local pixel
check. V5.21 already queued the historical V1/V3 overlap, so this experiment
tests the witness contract, not the V5.24 queue extension. First gate: Page23
must not silently preserve an overlapping shelf/panel split. All role,
partition, Dimension Engine, crop and ordinary V5 behaviour is V5.21.

SUPERSEDED EXPERIMENT, P0, V5.26 local-overlap witness projection: preserve V5.25's
V5.21 roles, partition and overlap-only queue. A model witness may be broader
than the compact corridor, but must overlap it by at least 4x4 px. Deterministic
code clips it to that local intersection before pixel audit and records both
raw and effective bboxes. This fixes the proven V5.25 false terminal failure
without accepting a remote witness or changing roles, partitions, crops,
Dimension Engine or ordinary V5. First gate: the V5.25 Page23 `view-003` /
`view-005` witness (850,380)-(920,450) against corridor (897,407)-(913,423)
must validate using effective witness (897,407)-(913,423).

REJECTED EXPERIMENT, P0, V5.27 source-degraded post-Discovery visual context:
the second call received padded candidate and nearby-pair crops beside the
complete 200 dpi page. Five Page23 runs produced the exact required grouping
only once. The crop queue used model-produced transport bboxes, so its claimed
adjacencies were false, including shelf plus lower console at zero pixels.
Review then used that context to falsely merge independent systems. Reject
static, candidate or pair crops before final inventory. Do not reuse V5.27's
crop-selection logic, but retain its telemetry as historical evidence.

FAILED QUALITY GATE, P0, V5.28 source-degraded direct inventory and
independent audit: four audited Page23 runs completed without crops or
validation errors, but all returned four final packages instead of shelf,
doors and the two console views as exactly three. Three runs were effectively
identical, with four assembly views and no positive relation edge at all. The
fourth made the angled shelving panel a same-page component of the shelf, but
still left both console views as separate objects. In every run the second
full-page call copied the first call's groups, roles and singleton partitions
rather than independently rebuilding the map. Its claimed console distinction
was vague "different component configuration and detailed labeling", not
concrete separation evidence. The owner constraint prevented an unowned
detail but did not establish physical continuity. Reject V5.28 as a quality
route. Do not tune its wording or re-run it. Its measured average is $0.02341
and 28.34 provider seconds per Page23 call pair. Ordinary V5, Fusion,
deterministic Dimensions and the source-degraded gate remain unchanged.

FAILED QUALITY GATE, P0, V5.29 source-degraded fixed-Island pairwise audit:
four Page23 runs were fully stable at five Islands, four technical plus title
context. The map correctly kept the continuous shelf intact and correctly
joined the two console projections through a concrete `alternate_projection`
edge. However, second-pass role assignment called the doors a
`component_detail` owned by the console without a `same_object` edge, direct
continuity, author label, matching dimensions or other owner proof. Because
the ledger compared only `assembly_view` pairs, the role removed doors before
the graph. All runs therefore returned two packages, shelf and console,
instead of three. The failure is a structural role-to-ledger bypass, not an
Island-map failure. Measured average: `$0.014472`, `19.25s`. Do not tune the
V5.29 wording or rerun it as an acceptance candidate.

FAILED VALIDATION, P0, V5.30 source-degraded pairwise preservation audit:
the first production run reached the second Haiku response, but a provider
returned a non-empty `owner_group_id` for an `assembly_view`. The schema
requires that field for every role, while the former direct-role validator
treated the irrelevant value as terminal. No Island, graph or package result
was produced. This is a role-field normalisation defect, not evidence against
the preservation contract.

FAILED QUALITY GATE, P0, V5.30.1 source-degraded pairwise preservation audit:
five Page23 production runs were stable at five Islands, four technical plus a
title context. The normalisation repair succeeded, but each graph linked shelf
to doors from a false `same_object` relation and left the two alternate console
views separate. The second call called the consoles merely similar and did not
record the full-object structural correspondence that V4.2 had used. The
route is not accepted. Preserve its neutral full-page map, no-loss role repair,
two Haiku calls and audit shape as V5.31's base.

FAILED QUALITY GATE, P0, V5.31 source-degraded pairwise structural audit:
four Page23 runs were identical at five Islands and exactly three published
objects, but the count concealed a wrong partition: shelf, console view one
and console view two. The model called doors a `component_detail` owned by one
console through a false `direct_continuity` claim, then called the two console
views distinct. The structural edge validator correctly rejected the
detail-console relation for graph insertion, but the older role resolver did
not consume that rejection and still removed the door Island before the graph.
The run therefore proves an ordering defect between role resolution and edge
admission, not a volatile visual-model result. V5.31 is not accepted.

ACTIVE EXPERIMENT, P0, V5.32 source-degraded structural admission for roles:
retain V5.31's fixed five-Island map, two complete-page Haiku calls, typed
structural witnesses and graph admission unchanged. A `component_detail` may
now suppress a technical Island only if its exact owner relation has passed the
same deterministic structural admission used for a graph edge. A rejected or
unadmitted direct-continuity claim promotes the Island to `assembly_view` and
records a role repair. No crops, Sonnet, ordinary V5, Fusion,
source-capability routing or deterministic Dimensions change. First gate:
Page23 retains doors as an independent technical object rather than silently
removing them. This is intentionally a one-factor recall repair; it does not
claim to solve the still-separate console views. Record role repairs, witness
ledger, rejected and admitted graph edges, Islands, packages, tokens, cost and
time before any next boundary experiment.

COMPLETE EXPERIMENT, NOT A RELEASE CHECKPOINT, P0, V5.32.1 source-degraded role wording and ledger completion:
preserve V5.32's Island map, two complete-page Haiku calls and structural graph
admission. Clarify that a finished separable fabrication, including a door or
door system, cannot become `component_detail` from plausible proximity,
material or installation alone. If the provider omits a required technical-pair
row, runtime appends only an audited `inconclusive` row with no visual evidence
and no graph edge. This prevents a formatting omission from failing a run, but
does not claim a missing relationship was resolved. First gate: Page23
completes with a visible runtime completion audit and preserves every technical
Island for review. Record original provider rows separately from runtime rows.

[verified, 2026-10-24] Five Page23 production runs were identical: five
Islands, four technical packages and one title context. Every provider response
contained all six technical-pair rows, so runtime completion was unused. The
model still called the door elevation a detail of one console; V5.32.1 promoted
it to an independent assembly because its claimed relation failed structural
admission. The two complete console projections remained `inconclusive`, so
the graph had no positive edge and published four objects instead of the
expected three. V5.32.1 fixes terminal pair-row loss and silent detail loss;
it does not solve complete-assembly pair interpretation and is not accepted as
a source-degraded Detection checkpoint.

REJECTED PRE-DEPLOY EXPERIMENT, P0, V5.33 visual embedding candidate prior:
before changing Detection or Railway, frozen `facebook/dinov2-small` was run
against the actual V5.32.1 Page23 Island bboxes at 96 dpi. Its intended
positive pair, the two alternate TV-console projections V3/V4, scored `0.4642`
and ranked last for both Views. False pairs V1/V4 and V2/V3 scored `0.8180`
and `0.8296` respectively and were mutual nearest neighbours. The model was
therefore trained and executable but unsuitable as an attention prior for this
technical-drawing identity problem. No V5.33 code, dependency, lockfile or
Railway deployment was retained. Do not retry DINOv2 embedding, tune a score,
or add it to ordinary V5. Any future visual encoder must first pass this exact
V3/V4 ranking gate without elevating a false pair. A core-bbox-only rerun
excluded annotation field and transport padding as the cause: V3/V4 fell to
`0.2987`, while false V1/V4 remained `0.8196`.

ACTIVE EXPERIMENT, P0, V5.34 unified rendered-page frame and bbox audit:
the ordinary V5 renderer now requests 200 DPI, matching the existing
source-degraded request. Rendering remains capped at 2,000 px on the longest
side. Diagnostics record requested DPI and each actual rendered page frame;
route labels no longer claim 96 DPI. No Island, crop, Fusion, semantic,
Dimension or graph rule changes. First evidence gate is a fresh Page23
source-degraded raw Island map overlaid on the exact 200-DPI JPEG frame. Then
audit the ordinary V5 proposal, static pre-Discovery regions, Fusion-to-JPEG
coordinate conversion and Review crops separately. Do not infer an Island
repair merely from the resolution change.

[verified, 2026-10-24] Fresh production Page23 run
`run_583c26209c264ac08040afad3b5dd66f` confirms the source-degraded page frame
is `1985x1404` at requested 200 DPI. Its five raw boxes still split the one
continuous shelf between `VG_P1_001` and `VG_P1_004`, and misplace
`VG_P1_003` over the lower left door rather than a TV-console projection. The
renderer is therefore now auditable but does not repair the primary map.

SUPERSEDED EXPERIMENT, P0, V5.35 native graphic-anchor Registry: retain the
source-degraded route only for a PDF where every rendered page contains 2-12
independent native image XObject placements, each covering 5-70% of the page.
Extract each source-authored placement into OCR/Fusion evidence with its PDF
point rectangle and map it deterministically into the actual capped rendered
frame. These are immutable candidate envelopes, not object claims: Registry
may assign their role and pairwise identity only, never draw, move, split or
replace their boundaries. The free Haiku Island-discovery call is skipped for
this source class. The remaining Haiku audit receives the whole page plus an
immutable labelled overlay, then returns the existing roles and same-page pair
ledger. Other PDFs, scans and ordinary V5 remain on their current routes.
First gate: Page23 must expose exactly the four authored drawing envelopes,
then yield shelf plus continuous panel, door system and two console views as
three object packages. Do not treat a correct envelope map alone as a package
quality pass. Record the route, source-anchor count, rejected placements,
overlay audit, cost and timing. If it passes, verify that a non-eligible
source-degraded file still takes V5.32.1 before considering a broader pack.

[verified, 2026-10-24] V5.35 re-ran the previously rejected frozen
`facebook/dinov2-small` diagnostic against the four source-authored Page23
XObject envelopes, not the former V5.32.1 model-produced boxes. The intended
two TV-console projections V3/V4 were mutual top-1 at cosine `0.8278` from
the native XObjects and `0.8316` from their rendered 200-DPI envelopes.
The false shelf-to-door pair V1/V2 was `0.4189` and `0.4440` respectively,
the weakest non-self pair. This reverses the V5.33 ranking failure because
the earlier input boxes were wrong, not because a score was tuned. The test is
diagnostic only: no production merge rule, threshold, dependency or deployment
was added. Before any integration, repeat its exact rank gate on a second
eligible native-XObject drawing and define an explicit negative rule so an
embedding can prioritize a pair for review but cannot independently merge it.

SUPERSEDED EXPERIMENT, P0, V5.36 native-XObject embedding pair priority: retain
V5.35's immutable source-authored XObject boundaries and all existing role,
ledger, witness and graph validators. For the narrow native-XObject route only,
extract the original embedded image bytes, run pinned offline
`facebook/dinov2-small@ed25f3a31f01632728cabb09d1542f84ab7b0056`, and append
only the same-page top-two cosine ranking to the existing Haiku pairwise audit.
The score cannot create a positive or negative relation, enter a witness, or
merge a package. It is recorded with all pair scores, rankings, model revision,
load status and elapsed time. Railway fetches its 88 MB DINOv2 assets at build
time and runtime loads local assets only. Warm model loading starts in the
native-graphic OCR worker, in parallel with Mistral, so an RFQ does not wait
for the first CPU initialization after OCR. Local build, offline load and 144
targeted tests pass. First production gate: Page23 must record an available
prior with V3/V4 mutual top-1, retain four immutable XObject Islands and never
publish an embedding-only merge. Do not extend this model to ordinary V5 or use
it as a numeric threshold until a second eligible native-XObject document
passes the same rank test.

CHECKPOINT, protected production, P0, V5.37 native-XObject embedding witness:
full record is `notes/DETECTION_V5_37_NATIVE_XOBJECT_EMBEDDING_WITNESS_CHECKPOINT_2026_10_24.md`.
V5.37 retains V5.36
native-XObject extraction, immutable Island map, role ledger and graph
validators. A conservative same-page mutual-top-1 pair with cosine at least
`0.80` and margin at least `0.10` over each member's next candidate becomes
typed evidence. The Registry must return its exact `embedding_reference` and
an assessment for every ledger row. For a strong pair, `different_object`
requires an explicit author distinction, incompatible visible dimensions or
physical separation of completed products. `same_object` may count the
embedding as one evidence item, but still needs a concrete independent visual
witness and two original assembly views. Embedding never creates a graph edge
alone. First gate: Page23 V3/V4 must cite `native_mutual_top1:0.8278`, produce
an admitted alternate-projection edge with a visible witness, retain four
immutable XObject Islands, and avoid a false V1/V2 or V1/V3 edge. This is
native-XObject-route-only, not an ordinary V5 rule.

[verified, 2026-10-24] Six independent production Page23 V5.37 runs were
identical: four native-XObject Islands, one admitted V3/V4
`alternate_projection` edge with exact `native_mutual_top1:0.8278`, and three
packages. V2's claimed V2/V4 ownership was rejected and V2 safely promoted to
standalone in every run. The package boundaries are accepted for Page23;
provider reasoning and naming for V2 are not. This checkpoint does not extend
the rule beyond the native-XObject route or establish cross-document validity.

ACTIVE IMPLEMENTATION, P0, V5.38 Railway DINO artifact caching: retain the
exact V5.37 Detection contract and model revision. Build the pinned DINO
artifact after the locked runtime layer and before application-source copy. A
normal code commit must not redownload the approximately 84 MB DINO weights
when Railway's standard layer cache is available. Verify the build image
contains the three required files, local-only runtime loading still works, the
V5.37 test suite passes, and a source-only deployment reuses the model layer.
Railway can evict build caches, so only a separately published image could
guarantee zero refetches after cache loss. This is a deployment-efficiency
change, not a Detection-rule change.

RESOLVED, USER-REPORTED 2026-10-25, V5.38 Railway Docker start-command override:
the Docker build, model-prefetch layer and Deploy stage succeeded, but Network
Healthcheck failed after 60 seconds. Railway Diagnosis attributes this to a
service-level Start Command overriding the Dockerfile `CMD` and passing the
literal `$PORT` to Streamlit without a shell. The owner then corrected the
Railway command configuration and confirmed the V5.38 deployment succeeded.
Do not alter the Dockerfile or Detection contract for this configuration-only
issue. The next deployment must still verify its own healthcheck and DINO
availability during a Detection run.

CHECKPOINT, V6.1, Detection document pre-analysis: the passive, page-level
technical profile is implemented and deployed. It records what each rendered
PDF page can provide deterministically, but does not change active Detection.
The profile is persisted in OCR evidence and Fusion diagnostics only. Page23
retained the protected three objects; HSL retained 10 final objects.

SUPERSEDED EXPERIMENT, P1, V6.2, expanded Fusion handoff: every bounded
page capability profile was sent to the ordinary Fusion Proposal and fixed-
Island Membership Review. The experiment did not demonstrate a quality gain
and added prompt volume. The active contract returns to V6.1: profiles remain
in the immutable OCR evidence and returned Fusion audit, but are not supplied
to either model call. The source-degraded route, router, models, candidate
regions, Candidate Q, embedding rules, deterministic graph and packages stay
unchanged.

REJECTED EXPERIMENT, P0, V6.3, no fixed pre-discovery page crops: ordinary
Registry Discovery briefly received only complete 200-DPI pages plus existing
Fusion text. The change removed the fixed `upper_left`, `upper_right`, and
`lower` crop set. It was not sourced from an Island, View or author-issued PDF
boundary, could show a physically continuous depiction in fragments, and
duplicated one full page-equivalent of pixels per page. The protected crop
contract is restored after the Adda regression below. Preserve 200-DPI
rendering, Mistral, Fusion, router choice, Candidate Regions, Candidate Q, the
source-degraded Page23 route and post-discovery View crops. A post-discovery
crop may remain a second-pass magnifier only, never create, split or move an
Island boundary.

Current 200-DPI local input measurement: HSL has 11 full pages and
added 33 fixed crops, 29,680,851 duplicated pixels and 2,854,649 JPEG bytes;
Adda has four pages and formerly added 12 crops, 11,312,000 duplicated pixels
and 830,268 JPEG bytes. These byte and pixel figures are not provider-token
estimates. Fresh production V6.3 runs confirmed `pre_discovery_region_count=0`.
HSL retained its active Island inventory, 10 packages and the same ten
review-required File Review rows. Versus the directly comparable fixed-crop
run, it saved 34,526 input tokens (142,539 to 108,013) and $0.036291
($0.187694 to $0.151403). Adda saved 12,120 input tokens (33,865 to 21,745)
and $0.041010 ($0.160950 to $0.119940), but regressed from two cross-page
commercial objects to eight page-local, review-required objects. Do not accept
token savings alone if the protected page-local inventory or commercial
boundaries regress. This experiment is rejected and the fixed Discovery crops
are restored. A later replacement must prove that post-discovery object/View
crops preserve Adda's cross-page grouping before it can eliminate them.

SUPERSEDED EXPERIMENT, P0, V6.4, route-scoped fixed pre-discovery crops: preserve
the V6.3 baseline for the deterministic `sonnet_boundary_risk` route only,
which is the unlabelled repeated-multiple-drawing-region condition that Adda
meets. Ordinary `haiku_default` Registry runs must pass `regions=[]` and no
longer construct JPEG crops. The router itself, model choice, Fusion, Page23
source-degraded route, 200-DPI rendered page input, Candidate Q, graph and
post-discovery Review crops are out of scope. Acceptance requires Adda retain
its protected two cross-page commercial objects, HSL retain the active Island
inventory, Page23 retain its protected source-degraded three-object result,
and usage confirm zero `pre_discovery_region_count` for HSL but retained
regions for Adda. Railway deployment titles for this and every later Detection
version must include the version identifier, using the versioned commit
subject as the deployment title.

REJECTED EXPERIMENT, P0, V6.6, single canonical View bbox on the Sonnet
boundary-risk route: retain V6.5 complete-page Discovery and post-Discovery
Review crops, but ask Discovery for only one `bbox` per Island. It is the
smallest View boundary containing the continuous drawing and directly attached
dimensions, labels and leader lines. The runtime mirrors it to the legacy
`core_bbox` only at the compatibility boundary, so Review crops and evidence
ownership use the same canonical geometry. Candidate Regions remain recall
aids, never bbox authority. This is router-scoped, not a filename rule: first
gate is Adda's exact two-object View membership, geometry and non-overlap.
The code is reverted to V6.5 after its first Adda gate. Do not extend this
contract to Haiku.

V6.6 Adda `run_e00376bd61e14f07a5e76d21a7d1bc49` fails that first gate: it
retains eight Object-Evidence Islands but produces four components, not the
protected two. Review correctly joins P2.V1/P4.V1 and P2.V2/P3.V2/P4.V2, but
leaves P1.V1 standalone and falsely joins P1.V2/P3.V1. Discovery also emits
overlapping canonical bboxes for the two P1 Islands and for the two P4 Islands,
despite the single-boundary contract. This rejects the one-bbox contract as
currently specified. Next diagnostic is a deterministic non-overlap/foreign-
Island admission audit before another prompt or routing change.

ACTIVE EXPERIMENT, P0, V6.7, Mistral graphic-anchor admission on the existing
`sonnet_boundary_risk` route: preserve the complete-page 200-DPI input, Mistral
OCR, Fusion, router, Candidate Q and Review, but elevate only Mistral `image`
blocks to initial page-local boundary anchors. Proposal returns one explicit
decision per anchor: `accept`, `tighten`, `expand`, or `reject`. `accept`
forces both effective Core and Envelope to the immutable Mistral bbox. A
`tighten` or `expand` needs cited page-local source facts and is rejected back
to the Mistral bbox if it captures another anchor centre or lacks the required
local evidence. `reject` requires the existing Candidate Region exception.
The raw Sonnet proposal and the deterministic admission audit are both retained.
This is a boundary contract only, not an object-identity, split or merge rule.
It must not activate for text-cluster candidates, ordinary Haiku or the
source-degraded/Page23 route. First live gate: repeat Adda and inspect all eight
anchor decisions, Island geometry, exact Counter/L-shaped View membership, and
two non-overlapping components before testing HSL or V-cabinet.

ACTIVE DIAGNOSIS, V6.7 first Adda gate: the successful live run
`run_632a5422f8264797901a286953aceb85` accepts all eight Mistral graphic
anchors and restores the intended applied P1/P4 boundaries. It still returns
three components: P2.V1/P3.V1/P4.V1 and P2.V2/P3.V2/P4.V2 are each correct,
while Review falsely merges P1.V1 and P1.V2 as one general-view installation.
This is not a V6.7 regression: pre-V6.7 run
`run_a51ffdbabcc64e79851ea8890e3a7bf5` made the same merge, while the earlier
correct run `run_d76e1c6d03374581aa84936676a5d8ad` produced the intended two
four-View components. Candidate Q contains all 28 final pairs, including every
P1-to-P2/P3/P4 pairing, but is supplied only to Discovery. Membership Review
receives no pair queue or draft hypotheses and records no negative decision for
the omitted P1 cross-page links. It instead gives the local P1 relationship a
direct, 100-point merge through an invalid "General View" explicit-document
relation. The review prompt is also internally contradictory: it asks to merge
continuous drawing extensions, then says continuity within one depiction is an
Island-boundary defect rather than pair evidence. Do not add an Adda-specific
ban. Before any identity repair, choose and test a general commercial-object
membership contract that reconciles P1-like perspective Views against existing
cross-page components, and rejects shared-sheet/composition continuity as an
author relation.

SUPERSEDED EXPERIMENT, P0, V6.8, bounded complete pair membership for the V6.7
Mistral-anchor route only: if the admitted object-evidence inventory has 2-10
Views, Membership Review receives the complete unordered matrix and must return
exactly one disposition for every pair: `same_object`, `different_objects`, or
`insufficient_evidence`. Only `same_object` may carry evidence. It needs a
direct cited document relationship or at least two independent typed facts, and
the existing deterministic semantic-ledger and merge policy validate those
facts before package membership changes. Dimensions may reinforce only a pair
that Review marked `same_object`; Candidate Q remains collected and audited but
is no longer the membership authority for this bounded gate. The pair matrix,
all dispositions, evidence counts, and timing remain in the run audit. This is
not a filename rule and does not activate for ordinary Haiku, Page23 or other
non-V6.7 routes. First and only live gate: run Adda, compare the two expected
four-View components with V6.7, then measure additional Review duration,
tokens, and cost before considering any broader route.

SUPERSEDED EXPERIMENT, P0, V6.9, criteria-then-reconciliation for the V6.7
Mistral-anchor route only: preserve Discovery and page-local Mistral boundary
authority. Membership now has three bounded stages. First, Review emits sparse
`preliminary_links`, each naming the exact pair and the first criterion that
made the pair worth testing. Second, Review must audit every preliminary pair
against all five criteria: identifier, topology, geometry, dimensions and
construction. Each criterion is explicitly `supports_same_object`,
`contradicts_same_object` or `not_visible`. Runtime, not model confidence,
computes a strong link: no contradiction plus either a direct supported author
relation or two supported discriminative criteria with two independent typed
evidence facts. Only strong links form transient reference components. Third,
every Island outside those components is compared to every reference component;
Review chooses a concrete member View for each candidate/component comparison
and again audits all five criteria. A final merge remains valid only through
accepted, cited pair evidence. General View titles, shared page, adjacency,
composition continuity, shared material, lighting and strokes cannot support a
criterion. This is not all-to-all and not a page-number rule. First gate is
Adda: retain all eight Mistral boxes, record the sparse preliminary links and
their five-criterion cards, create exactly four P1-to-component reconciliation
rows for a 3+3+2 preliminary result, and return the exact Counter and L-shaped
four-View memberships. Compare Review duration, tokens and cost with V6.7 and
V6.8 before extending any route.

PROTECTED EXPERIMENTAL CHECKPOINT, P0, V6.10, combined evidence review for the
V6.7 Mistral-anchor route only. Implementation is `1bd3c6e`, `c447b5c`,
`27e7e22`; full record is
`notes/DETECTION_V6_10_COMBINED_EVIDENCE_REVIEW_EXPERIMENTAL_CHECKPOINT_2026_10_25.md`.
Adda `run_c2ddd6be0c5b4add910d317382691d54` retained all eight Mistral boxes
and the exact two four-View memberships. It used two provider calls, 98.857
Detection seconds, 23,557 input tokens, 6,436 output tokens and `$0.167211`.
This is 31.1 percent faster and 29.5 percent cheaper than V6.9's true
three-call sum, while retaining the correct result. The aggregate event now
includes Proposal plus Combined Evidence Review. Conditional reconciliation did
not execute because every selected link was already strong. Do not generalize
this result, prune candidates, tune the prompt, or alter boundaries from this
one successful Adda run.

PENDING LIVE GATE, P0, V6.10 conditional reconciliation: before changing the
combined Evidence Review contract or expanding its route, run a document whose
sparse strong graph leaves an Island or component for reconciliation. Verify
the chosen reference member, all five criterion cards, exact final membership,
provider-call count, latency, tokens and cost. This is the first safe next
experiment after the protected Adda checkpoint.

OPEN DIAGNOSTIC, P1, V6.10 Adda local View-label ordering: page 1 assigns
`P01.V1` to the right/upper L-shaped view and `P01.V2` to the left/lower
counter, while pages 2 through 4 use the opposite positional order. Current
object membership is correct. Diagnose the source of local display ordering
without changing Mistral boxes, pair evidence, graph membership or package
boundaries merely to make labels look uniform.

PENDING DESIGN GATE, P1, document-scoped assembly classification: establish a
generic pre-membership category for drawings that describe one commissioned
assembly through an overview plus sections, component details, installation
context and hardware rather than multiple independently quotable products. The
first witness is `V_Cabiner.pdf`, a six-page vector-rich Order 1208 drawing
set. Do not route from filename, project/order number, repeated material or
page count. Existing `component_detail` is deliberately same-page-only and
must not be widened. Introduce a separate cross-page `part_of` relation within
an `assembly_set` scope, whose root may be one overview or a connected root
set. Dimension mismatch between an overall envelope and a carcass, module or
hardware detail is `non_comparable`, never negative evidence. A dimension may
contradict `part_of` only when both cited views explicitly claim incompatible
finished overall envelopes. Require a cited relationship graph from each
proposed member to the scope, using authored cross-references, visual
structural correspondence, component role, or other pair-specific evidence.
A page or Island without such a relationship remains a separate candidate,
never forcibly merged into the document scope. Detection must
preserve the component graph, source facts, quantities and confidence for
Estimation, while publishing one commercial assembly only when all included
members are evidenced. Decide the contract and benchmark before assigning an
implementation version or changing any current HSL, Page23 or Adda route.

ACTIVE EXPERIMENT, P0, V6.11 document-scope observation before Membership
Review: extend the existing full-page Discovery response with one validated,
compact `document_scope` decision. It is a semantic scope observation between
Discovery and Membership Review, not a pre-OCR router and not a fourth final route.
Allowed decisions are `assembly_set_candidate` and `ordinary_object_set`; an
assembly candidate needs a root/root-set and a cited hierarchy,
cross-reference or visual-component witness. Shared client/order metadata,
date, material, title block, page numbering and page count remain insufficient.
The decision is audit-only in V6.11: it must not affect Island boundaries,
Candidate Q, Dimensions, merge graph, commercial Objects or Estimation output.
Dimension mismatch is `non_comparable` unless two cited views explicitly claim
incompatible finished outer envelopes. First live gate: V_Cabiner returns an
auditable `assembly_set_candidate` with valid root and View witnesses;
inspect the resulting Island inventory and Objects explicitly, while no runtime
downstream decision may consume this field. Only after this shadow gate and
negative controls may a specialised `part_of` Membership Review be proposed.

ACTIVE EXPERIMENT, P0, V6.12 pre-Sonnet document categorization: replace the
former V4.2 binary model router with a deterministic scenario classifier that
consumes completed MyPDF/Mistral/Fusion evidence before any Detection-model
call. Categories are `source_degraded_visual`, `page23_native_graphic_pack`,
`assembly_set`, `ada_sparse_multi_object`, and `ordinary_object_set`; there is
no unresolved route, so all non-evidenced special cases default to ordinary.
`source_degraded_visual` remains a capability override for pages with no usable
coordinate evidence, while a source-degraded PDF with multiple native graphic
anchors retains the Page23 category. `assembly_set` is a routing class, not
proof of one final commercial object: its V1 gate is a continuous document
identifier across a majority of three or more structured technical pages, and
it must use Haiku. Only the remaining Ada-shaped boundary-risk category may
select Sonnet. V6.12 must not change Island boundaries, Candidate Q, graph
membership, scope observation, quantities or Estimation output. First live
route gates are V_Cabiner -> assembly_set/Haiku, Page23 -> native graphic pack,
Adda -> Ada/Sonnet, and HSL -> ordinary/Haiku. Audit each gate for category,
model, timing, cost, Island inventory and final Objects before considering any
membership work.

IMPLEMENTED, pending live HSL confirmation, V6.13 ordinary-proposal truncation
recovery: preserve the V6.12 category and model route. Retry Discovery exactly
once only when the initial proposal both consumes its 8,192-token budget and
ends inside a JSON string. The retry reuses the identical prompt, evidence and
images with a 12,288-token ceiling. All other invalid JSON fails immediately.
Persist both provider attempts and aggregate their measured time, tokens and
cost, so a recovered run cannot conceal the retry. First live gate: ordinary
Hasolelim HSL completes with the usual Haiku route, 35 Candidate Regions and a
valid proposal JSON. Do not treat this transport recovery as a change to
Fusion, Candidate Q, Island boundaries, routing, or membership.

VERIFIED, protected ordinary HSL checkpoint, V6.14 route-scoped scope
observation: V6.12 categorization has already selected the document scenario
before any Detection-model request, so ordinary, Page23, Ada and degraded
routes must not ask Discovery to re-classify document scope. Remove
`document_scope` from their prompt, strict output schema, audit payload and
provider response. Preserve it only for `assembly_set`, where V6.11 continues
as an audit-only observation and runtime now enforces its four roots, four
witnesses, four IDs per witness and 180-character observation bounds. Keep
V6.13's one-time truncation recovery as a rare transport safeguard, not a
normal ordinary-path cost. HSL `run_e8006a40e1fe4c68846b59b44dacaf4c` stayed
`ordinary_object_set`/Haiku, completed without retry at `$0.151403` Detection
cost, and retained 32 object-evidence Islands in ten components. Its page-2
floor plan was discarded document context. This protects the ordinary route
only. Deferred Naming and Preview defects remain separate, and future HSL
audits must preserve the full inventory, membership and cost evidence.

FAILED LIVE REGRESSION, V6.15 document metadata and
object-bound Naming evidence: retain the existing Naming prompt, locked object
identity, quantities, route selection, Discovery/Review sequence and
Estimation package. The existing Discovery response now carries one compact,
source-fact-cited sidecar for `project_name`, `design_partner`, `client`,
`author` and `document_date`; unknown is valid only without a citation. The
run record materializes those values while the citation audit stays in the
Detection usage event. After Registry locks its Islands, each object's final
Island bbox is added to its evidence refs and produces ephemeral Naming crops
in the same coordinate frame. Deferred Naming receives those object-bound
crops and only spatial OCR whose centre falls inside a locked Island. It no
longer receives full document pages on the V6.15 path. Explicit administrative
labels such as `Revision log` and `Surface schedule` are rejected as object
names. This must not change Island boundaries, object membership, quantities,
the Naming prompt, or the ordinary HSL route. Live gates: HSL must retain
ordinary/Haiku, 32 object-evidence Islands and ten components while filling
source-supported document fields and avoiding sheet-administration names;
then Page23 and Adda must retain their protected object boundaries. The first
ordinary HSL live gate failed: `run_07934b6dcbbc48bda1da8ea96e4d7d93` remained
on the ordinary Haiku route but produced 33 object-evidence Islands and 14
components, versus V6.14's 32 Islands and ten components in
`run_e8006a40e1fe4c68846b59b44dacaf4c`. The added metadata was requested from
the same mandatory Discovery response that owns Island discovery, so it is not
operationally isolated despite being described as audit-only. Its observed
values also did not meet semantic-role acceptance. Separately, the intended
object-bound Naming path did not run: the audit recorded `crop_count: 0` and
`objects_with_crop_count: 0`, so Naming fell back to whole pages. The cause is
that final normalized visual groups do not retain `evidence_class`, while the
crop helper filters strictly for `object_evidence`. Do not promote or extend
V6.15. Return to the V6.14 protected contract before a replacement experiment;
the replacement must obtain metadata outside the Discovery response, use real
Registry-owned crops, and pass HSL's 32-Island/ten-component gate before
Page23 or Adda regression.

FAILED RUNTIME OBSERVATION, V6.16 isolated document identity and locked Naming
evidence: the code passed focused local tests and preserved the V6.14 Detection
path by construction, but the first production attempt appeared to stall before
it produced a run ledger entry. It was reverted immediately to keep the V6.14
checkpoint live. A subsequent browser attempt reportedly completed, but no
corresponding run appeared in the queried production ledger, so the alleged
stall is inconclusive and must not be attributed to the document-identity code
without a correlated run ID.

ACTIVE, approved V6.17 isolated document identity, source-index Naming and
File Review metadata: preserve V6.14 Discovery, Review, routing, Islands,
proof graph, package membership and Evidence boundaries byte-for-byte. After
Registry has locked objects and File Review has been saved, derive a private
sidecar containing only each Registry-owned View ID, page and existing bbox.
Use that sidecar to make Naming-only crops and local OCR retrieval. Assign
only empty, `Unknown`, `Unlabelled`, `Untitled`, or generic `Object N` labels a
visible deterministic provisional name `Object 01`, `Object 02`, and so on.
Keep every recognized source code, including letter-suffixed `N76B` and
numeric-leading `7-6B`, as the final-name prefix followed by the semantic
description. Move File quality into Technical metadata only. The title-block
result must update the editable Project, Partner and Client fields in the
existing File Review without a full app rerun. The following V6.16 scope is
retained as V6.17 implementation detail:
preserve V6.14 Discovery, Review, routing, Islands, proof graph, package
membership and Evidence boundaries byte-for-byte. After Registry has locked
objects and File Review has been saved, derive a private sidecar containing
only each Registry-owned View ID, page and existing bbox. Use that sidecar to
make Naming-only crops and local OCR retrieval. Do not use full-page Naming
input when every locked object has a crop; retain the existing full-page path
only when a complete crop set is unavailable. In a separate deferred call,
read bounded title-block corner crops and update only still-`unknown` run
fields. `Project` maps only to project_name; `FILE NAME`, drawing identifiers,
logos and addresses cannot establish project, client or partner. Client and
Partner remain `unknown` unless their roles are explicitly visible. Neither
branch can add, remove, merge, split, reorder or rename Detection packages.
Gates: ordinary HSL remains 32 object-evidence Islands and ten components;
Naming receives nonzero Registry-owned crop evidence and returns category plus
source index where supported; HSL title block yields Project `ROOMS`, author
`Ayelet Levit`, document date `09.09.2025`, and no false Partner from
`Hasolelim_Carpentry`; Page23 and Adda then retain protected boundaries.

ACTIVE, approved V6.18 OCR-grounded document metadata and drawing indexes:
replace the unbounded deferred image-model identity call, which scheduled but
never emitted a terminal event in HSL `run_ff729e5345604d70a9f757fc4695bb76`,
with deterministic extraction from the already persisted Mistral OCR evidence.
The OCR fact `PROJECT -> ROOMS` is sufficient only for `project_name`; it does
not establish Client or Partner. Before locked Naming input is made, use only a
literal `DRAWING NAME -> code` title-block fact on an object's already locked
evidence page to replace an `Object NN` placeholder. Thus `N57`, `N60`, `N68`,
`N70`, `N76`, `N76B`, or other literal author codes can prefix the subsequent
semantic name, while an absent or conflicting code remains `Object NN`. Remove
Project name, Partner and Client from Technical metadata because they already
have editable fields above it. This must not change Detection's object count,
package membership, quantities, Island inventory, route, or Estimation package.

ACTIVE, approved V6.19 annotated source-page Naming experiment: supersede only
the V6.17 object-crop input contract. Preserve V6.14 Detection, Registry
membership, OCR, router, object order, quantities, source codes and Estimation
evidence. After Registry locks its View ownership, render each physical source
page containing at least one Registry-owned View once at the existing rendered
page resolution. Overlay every locked View bbox without fill. Each overlay must show
the immutable `object_id`, and every View belonging to one object must use the
same label and colour across pages. Naming receives those annotated full pages,
the existing locked object mapping and bounded OCR facts. It may return only a
semantic name suffix. It cannot alter object count, ownership, source index,
quantity, bbox or package membership. Record page count, source page numbers,
encoded image bytes, overlay View count and overlay-render audit in the
Detection usage event. First live gate is HSL: ordinary Haiku Detection remains
32 Islands and ten objects, Naming emits a terminal event, and the request
contains one annotated page per Registry-Island page rather than one crop per
View. Compare Naming duration, tokens and cost with V6.14 before extending the
experiment to Page23 or Adda.

LIVE AUDIT, V6.19 HSL `run_a209ce477a914e63a277ade7a6577e2e`: Detection
preserved the protected ordinary Haiku result, 32 Registry-owned Views and ten
objects. The overlay contract also materialized correctly: nine annotated
source pages (P3-P11), 32 overlays, ten object labels and 2,139,216 encoded
image bytes. However, no `locked_object_naming_deferred` terminal event exists,
neither success nor failure. The current File Review therefore shows only
deterministic source indices, not a semantic Naming result. Do not evaluate
V6.19 naming quality or cost from this run. The immediate diagnostic must add
nonblocking durable lifecycle evidence that distinguishes submitted, worker
started, provider returned and terminally persisted Naming. Separately, File
Review has two unconditional `run_every=2.0` fragments. The dynamic fragment
refreshes even without deferred work, and the metadata branch never marks its
document-identity flag complete. This is the supported cause of its perpetual
two-second refresh cycle; repair that UI lifecycle independently from Naming.

SUPERSEDED INPUT CONTRACT, V6.5, no static pre-Discovery crops: remove the three
fixed `upper_left`, `upper_right`, and `lower` images from the Adda
`sonnet_boundary_risk` route as well as the ordinary Haiku route. Retain the
same 200-DPI complete rendered pages, Fusion, Candidate Regions, router,
model route, Candidate Q, Review page contexts and post-Discovery View crops.
This isolates whether a page grid which cuts an authored drawing before its
Island is known causes the unstable Adda proposal/review result. First gate is
Adda: exactly two non-overlapping commercial components with counter Views
`P1.V2,P2.V1,P3.V1,P4.V1` and L-shaped cabinet Views
`P1.V1,P2.V2,P3.V2,P4.V2`. The next gates are unchanged Page23 and HSL
protected inventories. A no-crop result with two objects alone is insufficient:
the exact View membership and per-page Island geometry must also pass.

OPEN DIAGNOSTIC, P0, V6.4 Adda Registry instability: compare completed Adda
runs `run_d76e1c6d03374581aa84936676a5d8ad`,
`run_6776dd3ea03040c9b38f8d060863001a`, and
`run_f35b802961ce49d094759890fd42e7cc` before changing the active contract.
Mistral Candidate Regions are byte-for-byte stable at the correct page-local
boxes for pages 2 and 3, but Discovery redraws its own `visual_groups` boxes
from the full page plus static crops. The second proposal's page-2 L-shaped
envelope begins at x=490 instead of the candidate x=913, while the latest
proposal returns a corrected core. Review receives only those model-drawn
groups and their derived crops, so it cannot recover a discarded candidate
boundary. The latest Review also emits an overlapping counter hypothesis;
runtime rejects that duplicate, retains its earlier incomplete three-view
hypothesis, and consequently packages the missing page-1 counter view as a
third standalone object. Establish, by a narrow A/B, whether the fixed
upper-left/upper-right crop boundary, which cuts the page-2 L-shaped drawing,
is causal, and then propose a candidate-region-to-Island admission contract.
Do not treat image XObjects as object boxes: Adda has zero Form XObjects and
only small raster placements; its object-level candidate boxes come from
Mistral graphic regions.

DEFERRED, P2, USER DIRECTION, Detection input and cost optimisation: begin
only after the owner concludes the current correctness experiment. Assess the
full-page Evidence Inventory, Candidate Pair Q prompt rendering, static crops,
review images, output budgets and any other input/output reduction by isolated
benchmark, while retaining the underlying evidence, Q calculation and
deterministic graph unless separately approved. Do not treat HSL's currently
unreferenced facts as globally removable.

DEFERRED WORKING BLOCK, P1, USER DIRECTION, visual matching, geometry evidence
and Estimation preparation: begin only after the owner accepts the current
Detection correctness experiment. This is research and a benchmark plan, not an
approved replacement of Detection, Fusion, routing, DINO, Candidate Q or the
Estimation contract.

Current verified system map:
- Candidate Regions are recall bounding boxes, not a similarity engine. They
  originate from Mistral `image` blocks, or broad spatial clusters of evidence
  facts if no graphic block exists. They never identify objects or compare
  views.
- Candidate Pair Q / Dimension Fingerprint / Weighted Similarity is the
  deterministic mathematical comparison channel. It evaluates normalized
  dimension-chain values, occurrence, page context and normalized Island
  placement. It supplies supporting evidence only and cannot merge a commercial
  object by itself.
- The current DINO channel is `facebook/dinov2-small`, 384-dimensional global
  CLS embeddings of source-authored PDF image XObjects. It is limited to the
  narrow source-degraded native-anchor route, compares same-page placements,
  and requires mutual top-1, cosine >= 0.80 and margin >= 0.10. It remains
  visual supporting evidence and never creates an edge alone.
- Current Mistral is `mistral-ocr-4-1`, with `include_blocks=true` and block
  confidence requested. Its raw blocks, page confidence and provider response
  are retained. Normalized Fusion text facts currently retain block type, text
  and bbox, but do not copy each block's confidence values into the derived
  facts. This is a possible later quality signal only, never geometry proof.
- V6.1 PyMuPDF inspection already inventories text, image XObjects, Form
  XObjects and bounded vector summaries. `get_cdrawings()` / `cluster_drawings()`
  are not semantic dimension-line extraction and must not be sent as raw vector
  dumps to a model.

Research evaluated:
- DINOv2 can also yield patch features. Test only as a bounded local-
  correspondence supplement for already eligible, visually similar 2D views;
  it must not become an embedding-only merge rule.
- DINOv3 may be benchmarked against DINOv2 only after a license/product review
  and a measured CPU/Railway artifact experiment. It is not a current upgrade.
- LightGlue is a local-feature matcher, not a semantic or 3D-view matcher. It
  may help only with near-duplicate, scaled or rotated 2D depictions after a
  licensed detector and geometric inlier validation are chosen. It is not a
  general solution for front/side/top orthographic views.
- SigLIP 2 is potentially useful later for broad semantic retrieval or
  classification, not commercial-object identity, dimensions, materials or
  quantity.
- SAM 3 could create optional candidate masks in raster-heavy pages, but there
  is no evidence it is a strong vector technical-drawing solution. Its model
  license and resource requirements require separate review.
- MASt3R is excluded from product implementation: its published license is
  CC BY-NC-SA 4.0 and its evidence concerns photographic multi-view matching,
  not engineering projections.

Highest-value proposed research direction: an object-bound, line-aware
geometry-evidence extractor inspired by Martin Riegelnegg's 2024 TU Wien
diploma thesis, "Automated extraction of complexity measures from engineering
drawings." The thesis uses entity segmentation, arrowhead / dimension-line
processing, object-view segmentation, orthographic view-grid reconstruction,
axis assignment and OCR-to-pixel consistency. Its reported 0.731% mean
absolute external-dimension percentage error applies to 81 of 84 selected
detail drawings after excluding three OCR-failed cases. It is not evidence of
accuracy for Costerly's multi-object carpentry sheets, plans, schedules,
perspectives or incomplete drawings.

Target boundary, not current behavior:
Detection locks commercial-object identity, quantity and cited evidence pages;
then an eligible object-specific geometry stage emits auditable candidates;
then Estimation interprets construction / Material Demand; Resolver, Material
Engine and Labor Engine remain deterministic. Geometry output must preserve
page reference, object/view bbox, dimension-line bbox, linked OCR literal,
arrow/line orientation, scale-ratio consistency, axis hypothesis and conflicts.
It returns `not_applicable` or `review_required` rather than invented W/H/D,
materials, BOM or labor facts. Presentation Preview remains UI-only.

Eligibility and verification before any integration:
- operate only on object-bound technical detail/elevation/section evidence with
  readable dimensions and adequate raster or vector geometry; exclude schedules,
  title blocks, whole floor plans and unsupported perspectives by default;
- create a manually labelled geometry benchmark of object-bound furniture
  detail views, not Page23 alone; record source line to dimension literal,
  external axis/value, unavailable cases and false associations;
- compare current literal-only evidence against the line-aware candidate output;
  define precision, recall, conflict and `not_applicable` acceptance criteria
  before coding; do not promote a value to Estimation merely because it is
  numerically plausible;
- independently measure CPU, memory, latency, model artifact size, provider
  tokens/cost, license fit, HSL / Adda / Page23 regressions, and evidence-package
  compatibility before any product decision.

SUPERSEDED IMPLEMENTATION, P1, V6.1, USER DIRECTION, Detection document pre-analysis:
define a non-decisive,
page-level technical profile that records what each rendered PDF page can
provide deterministically. It must report native text availability and quality,
image XObject/Form XObject/vector-drawing inventory, rendered-page properties,
visual density and structural complexity, coordinate-bearing evidence
capability, and the cost/timing of every local inspection. The document result
is a list of immutable page profiles plus a derived summary, never one global
document type. Run it asynchronously or in parallel with the existing
PyMuPDF/Mistral work, persist an audit even if it finishes after Registry, and
do not let failure, output, model choice, Island
inventory, Dimensions, graph, packages, or File Review change during this
observation phase. V6.1 explicitly passes the compact profile audit through
Fusion diagnostics but does not add it to the Registry prompt. Acceptance
requires no-behavior-change evidence plus measured incremental critical-path
latency for Page23, HSL and Adda.

Native PDF image XObject placements are already extracted for every PDF in the
OCR worker and retained as `evidence.graphic_regions`; however, the ordinary
Fusion candidate builder currently consumes Mistral graphic regions or text
clusters, not those native placements. Treat every XObject bbox as a
source-authored graphic envelope and recall/diagnostic input only, never as an
object boundary or merge proof. The existing V5.37 immutable-anchor gate stays
separate and narrow: all rendered pages must have 2-12 independent eligible
image placements, each covering 5-70% of its page. Do not broaden that gate or
add embedding to ordinary PDFs without a separate approved experiment.

Later decision: replace layered router mutation with one auditable
`DetectionExecutionPlan` composed from independent axes, including evidence
path, boundary-risk model, Island-anchor authority and optional embedding
availability. Do not merge their criteria into one "complex document" score.
First verification artifact: profiles and no-behavior-change traces for HSL,
Page23, Adda, and a mixed-evidence PDF, including identical current routing and
Detection outputs plus measured incremental CPU, memory and critical-path
latency. Only then decide the mixed-evidence contract and whether native
XObject recall is admissible in ordinary Fusion.

ACTIVE DIAGNOSIS, P0, Processing to File Review client transition defect:
the same run completed Registry in 23.28 seconds and server-side File Review
in 26.67 seconds, while the browser recorded a 15.001-second
`processing_to_file_review` timeout. The current browser readiness predicate
requires `.file-review-card`, but the renderer produces
`.file-review-summary-card-marker` instead. This prevents the browser from
acknowledging the already-rendered File Review and leaves the Processing shell
visible. Do not alter Detection, OCR, or provider timeouts. The repair must
align the browser predicate with the actual File Review marker, retain the
existing 120 ms handoff, and be verified in an authenticated production cycle
by a terminal `browser.transition_ready` rather than only a server render.
The marker-contract repair and regression test are implemented locally. Production
verification remains required before this item can be closed.

DEFERRED, P1, USER REQUEST, Detection Processing provider-outage handling:
when Mistral OCR is unavailable, exhausted, rate-limited, or times out, the
Processing screen must never remain at its initial elapsed value. Persist a
safe early lifecycle marker before OCR, record a terminal OCR failure/timeout
with its stage and duration, and show truthful pending/fallback state while
the bounded no-OCR route runs. If the run cannot continue, expose a retryable
terminal state rather than an infinite Processing screen. Preserve the normal
parallel OCR path and do not add a second Detection call. Acceptance requires
a forced Mistral 402 and a forced timeout to reach an observable terminal or
explicit fallback state without leaking credentials or file content.

BLOCKED QUALITY GATE, V5.9 HSL `v590-hsl-04`: the cross-document run rejects
the experiment in its current form. It returned 31 raw Visual Groups, 28
Object-Evidence Islands and 12 packages, rather than the protected HSL 32/9
orientation. P03 has two rather than three Object Islands; P07 remains four
single packages; P09 splits into two; P11 has three groups but classifies every
one as Document Context, leaving no package. The Proposal cost `$0.158686`
and took `61.559s`; Review cost `$0.027967` and took `22.358s`; combined
provider time was `84.788s` (`110.223s` end-to-end). Do not tune package merge
or Semantic facts from this result. The next causal repair, if approved, is
Island segmentation: one physically continuous visual depiction is exactly one
Island even if its silhouette bends, branches or is highly non-rectangular.
Its bbox is only a padded rectangular transport envelope around that complete
connected depiction. A split continuous shelf and panel is an Island defect,
not two Views to repair downstream.

CONFIRMED ROOT CAUSE, before any later Island-reconciliation experiment: V5.9
has no explicit coordinate-frame transform between Fusion and Review. Native
MyPDF spans and Mistral OCR/graphic Regions are produced at 200 dpi; Registry
Proposal/Review pages are rendered at 96 dpi. Page23 measures 3308x2339 in
the Fusion frame and 1588x1123 in the Review frame. Proposal emitted a
Fusion-frame bbox through x=3265, but Review cropped and overlaid it directly
on the 1588-pixel image. The second call therefore receives displaced or
clipped View crops and misplaced Island labels. This invalidates V5.9 Review
quality conclusions, including its HSL segmentation result. The isolated
Page23 geometry gate now passes locally: all 200-dpi Fusion bboxes transform
to their 96-dpi Review locations, including VG-005 x=1600..3265 becoming
x=768..1567. External run `v590-coordinate-page23-02` independently confirms
the recorded Mistral 3308x2339 to Review 1588x1123 frame, 4 object Islands and
3 packages: shelf, doors, and the linked two-view TV console. It costs
`$0.022186` and takes 32.375 seconds wall time. Coordinate correctness is now
verified for Page23, but this does not validate HSL segmentation or justify
continuity unions or semantic tuning.

V5.10 benchmark state, 2026-10-23: Page23 `v590-coordinate-page23-02`
passes its discriminating boundary at 4 Object Islands and 3 packages. Adda
`v510-adda-01` produces 8 Object Islands and 2 packages, so its package count
is compatible with the known two-object case but Island membership still needs
inspection. Metal `v510-metal-01` fails the universal merge gate: 30 Object
Islands become 28 packages, including five separate packages each on P04 and
P05, versus the roughly 13-15 expected commercial objects. HSL `v510-hsl-01`
did not produce a result, because Proposal JSON truncated in an unterminated
string after 25,358 characters. This is an output-contract failure, not an
Island-quality result. V5.10 is not a checkpoint. First recover a complete HSL
Proposal response without weakening Island or membership evidence, then inspect
Adda membership and Metal page-level boundaries.

P1, pending, V5.10 benchmark failure-cost observability: the local runner
currently records only `repr(exc)` after a failed provider call and drops the
exception's available usage event, so the HSL failed-call cost is unknown in
its local report. Persist safe usage totals and diagnostics on failure, without
logging secrets or retrying automatically.

V5.10.1 HSL `v5101-hsl-01` proves that Proposal output compression is safe for
Island recall: it completes JSON and returns the required page-level Island
inventory, but all Review facts were rejected because the handoff represented
an ID and its text as `SF00123:text`. V5.10.2 `v5102-hsl-01` uses bracketed
source IDs and returns 33 Object Islands, 12 packages, 27 accepted semantic
facts and 21 merge edges. Page-level HSL Island counts meet the active
benchmark: P03=3, P04=6, P05=3, P06=3, P07=4, P08=4, P09=3, P10=3, P11=3.

V5.10.3, verified locally without a provider call: canonicalise only a source
ID in the exact display form `[SF00123]` when the interior `SF00123` is already
known in that run's evidence. Keep the raw Review response unchanged and write
every conversion to `source_id_normalizations`; unknown wrappers remain
rejected. Reprocessing saved HSL Review `v5102-hsl-01` accepts all 65 of its
semantic rows, records 65 such canonicalisations and leaves zero unknown-source
rejections. This validates citation transport only, not the commercial merge
outcome. In particular, P04 may legitimately contain one to three products, so
its package count is not a quality gate. The next provider run must compare the
same page-level Island inventory and View membership, not force P04 into one
package or toward a global count of nine.

V5.10.3 HSL provider run `v5103-hsl-01`, 2026-10-23: the source-ID repair
holds in the complete cycle. It returns 63 accepted semantic facts, no accepted
bracketed source IDs and no `unknown_source_fact` rejection. HSL keeps the
required Object-Island counts on P03-P10, P04=6 and P11=2 Object plus 2 Context
Islands, which are both within the permitted inventory range. P04 produces one
package, an allowed outcome. The run is not a checkpoint because P02's generic
floor plan is again classified as `object_evidence` and published as a singleton
package. The existing generic-plan safeguard did not apply because Registry
mislabelled its `representation_kind` as `object_evidence` instead of
`floor_plan`. Diagnose and repair that classification-contract breach in
isolation before any package or graph tuning. Timing: 165.346 seconds total,
Registry cost $0.206013.

P1, pending, V5.6.10 semantic criteria: stricter `matching_topology` and
`direct_shared_structure` wording was not regression-proven. Re-evaluate it
only after the V5.7.1 boundary strategy is measured across the MVP pack.

Historical V4 notes follow. They are retained for rationale, not the active
implementation plan.

HISTORICAL, Detection V4 commercial-boundary stability: protected checkpoint
`52c314d` retains accepted Naming, File Review, temperature-zero, complete
Evidence, and Page 23/Adda boundary behavior. Hassola LIM is the active
boundary benchmark. The MVP floor is now 9 commercial packages: N56, N57,
N60, N62, N68, N70, N74, N76, and N76B. N57 may remain one review-required
source-root package with all its Evidence, while Estimation later decides
whether to split kitchen, island and tall cabinet. The active V4 candidate
requires every retained object-evidence island to have exactly one package.
Shared physical-page Evidence remains freely reusable.
This adds no model call, router, Sonnet route, or file-specific override.
Preserve object-ID locking, full object evidence, UI-only previews, deferred
Naming, File Review timing, and TC. Next gate: fresh HSL run must produce the
9 packages with complete page-4 Evidence, then regress Page 23 and Adda.
Current model build: `Detection V4.43`, experimental, built on the protected
V4.23 passive OCR cross-check and checkpoint `52c314d`. Comment: V4.12 still
treated every N76B page-11
depiction as a partial component, then attempted to attach all three to N76B.
The failure proved that assembly/component was an invalid eligibility gate, not
that their source Evidence was wrong. V4.13 allowed any full view or detail to
support an object, but still let the model declare membership twice: a group
could be object evidence yet be omitted from the object's group list. V4.14
removes that duplicate ownership declaration. Every visual group is
object-specific Estimation Evidence and names one or more owners locally; code
derives each object's group package from that ledger. Cover/title pages,
generic floor plans, room layouts, electrical, plumbing, lighting, legends and
other non-object-specific pages make no visual group and have empty Evidence
coverage. Detection may still use them for metadata, sheet codes or navigation.
V4.15 preserves that ledger and replaces loose merge-proof type labels with
typed, page-attributed visual facts. The evidence order is explicit document
relation, dimension transform, matching topology, unique geometry, then direct
shared structure. At that stage, a non-explicit merge needed two independent
facts and at least one identity-level fact; direct shared structure alone
cannot merge.
V4.16 discards generic floor plans, title pages and title blocks from the
effective visual-group payload before ownership, proof construction, identity
pages and Estimation Evidence. An object-specific plan remains eligible only
as `object_plan`. This adds no model call, router, Sonnet path, Naming or UI
timing. V4.17 replaces the V4.14 owner ledger as the source of object
membership. The model now returns only object-specific visual groups, typed
pairwise merge facts, one component descriptor per proof-graph component, and
page coverage keyed by that component descriptor. Runtime derives every
commercial object and its `visual_group_ids` solely from the connected proof
forest, assigns ordered runtime object IDs, then resolves Evidence coverage.
An unlinked group is a singleton object, a multi-group object cannot exist
without its minimal proof tree. A physical page remains reusable Evidence for
several components, but one visual group cannot be an owner declaration for
several objects. No model call, router, Sonnet path, Naming or UI timing is
added. The HSL V4.17 failure showed that an optional top-level proof array can
still be omitted while the model returns a smaller set of object descriptors.
V4.18 replaces that optional array in the model contract with one required
`proof_parent` decision on every visual group: either `new_object_root` with a
factual reason, or `attach_to_group` pointing only to an earlier group with
typed evidence facts and a factual reason. Runtime derives the same proof
forest and object packages exclusively from these group-level decisions, and
persists every decision and its answer to "why" in the Registry audit. This
adds no model call, router, Sonnet path, Naming or UI timing. It is not a
checkpoint until HSL produces the canonical 11 packages with complete
object-specific evidence, followed by Page 23 and Adda regression gates.
V4.19 permits one exact `dimension_transform` as a sufficient attachment fact:
it must name measurements on both views and their axis or unit transformation.
"Compatible" dimensions, similar scale or one repeated number are not enough.
All other non-explicit attachments still require two independent typed facts.
V4.20 requires a persisted `dimension_assessment` for every root-or-parent
decision. Before an attachment, Detection compares readable dimensions after
document-wide unit normalization and projection/axis transformation. A
confirmed match can support the existing `dimension_transform` fact. A
confirmed conflict in the same physical axis and scope is a structural no-merge
condition, including when a shared code or sheet might otherwise suggest a
relation. It must become a root with the rejected group's ID and conflicting
measurements in the persisted factual reasoning. Different axes, whole-object
versus local-detail measurements, quantities, scale or missing readable values
are explicitly recorded as not comparable or insufficient, never treated as a
conflict. No model call, router, Sonnet path, Naming or UI timing is added.
V4.21 retains the same dimension-conflict guard but replaces the verbose nested
assessment with a compact required `dimension_status`; the existing mandatory
`decision_reason` remains the factual explanation, including rejected group and
measurements for a conflict root. This avoids exhausting the Registry output
budget on repeated explanation. JSON parse failures now persist a failed
Registry usage event with response length, SHA-256, provider stop reason and
token budget, so truncation versus malformed provider JSON is observable.
V4.22 makes the compact `dimension_status` bidirectional with typed evidence:
`confirmed_match` is valid only with an exact `dimension_transform` fact naming
measurements on both groups and their transformation, and that fact requires
`confirmed_match`. A bare status is never merge evidence. This prevents a
model's generic claim that dimensions agree from bypassing the independent-fact
threshold for a section or alternate view.
V4.23 removes that duplicated positive representation: an exact
`dimension_transform` is now the sole source of a positive dimension match.
When a same-scope dimension conflict rejects one plausible earlier group,
Detection must search every other earlier object-specific group before it
creates a root. It may attach only to an evidence-backed non-conflicting group;
otherwise the root persists a typed `blocked_merge` naming the rejected group
and both incompatible measurements. This preserves the critical no-merge rule
without forcing the model to serialize the same conclusion twice. It adds no
model call, router, Sonnet path, Naming or UI timing.
V4.24 and V4.25 were rejected experiments: making OCR `image` regions a
Registry coverage contract, then requiring a new all-island output, caused
Haiku to classify the entire HSL package as administrative. The active V4.23
cross-check instead appends the same OCR graphic-region coordinates as a
passive visual re-inspection aid. The model first identifies Visual Groups from
rendered pages using the protected V4.23 contract, then may revisit an OCR
coordinate. OCR can neither create, split, merge nor invalidate an object, and
no response field or validation requires equal counts. Runtime persists raw
OCR-region and Visual-Group counts by page on successful and failed Registry
events. No model call, router, Sonnet path, Naming or UI timing is added.
Visual Group discovery gate is provisionally met: the HSL audit found all
three N56 depictions despite only two OCR regions, and four different
subsequent files preserved or exceeded their OCR depiction count. Checkpoint:
`notes/DETECTION_V4_23_PASSIVE_OCR_VISUAL_DISCOVERY_CHECKPOINT_2026_10_19.md`.
Next gate: diagnose and repair HSL pairwise merge proof failures without
changing this protected visual-discovery contract.
V4.26 is the approved one-call structural experiment. It preserves the complete
visual-island search, passive OCR audit and temperature 0, but replaces the
incremental `proof_parent` decision with explicit staged output: complete island
inventory, mandatory `object_evidence` or `document_context` classification
with a factual reason, full typed proof graph between any object-evidence
groups, and finally packages derived by code from graph components. A document
context may not enter the proof graph. The audit persists classification reasons,
every graph observation and each package's boundary/Evidence reasons on success
and validation failure. Acceptance requires successful V4.26 runs with this
audit, then Page 23 and Adda regressions before HSL package quality is judged.
V4.27 keeps the one Haiku call, temperature 0, passive OCR recall aid and the
same proof/package rules, but serializes the response into five non-overlapping
phases: visual-island inventory, exact-once classification, global proof graph,
component packages, then page coverage. Inventory cannot carry a class; each
group receives exactly one later factual classification without changing the
inventory. The prompt also prohibits coalescing separate side-by-side views,
facades or dimension depictions into one island. Classification, graph and
package reasoning remain persisted on both success and validation failure.
Acceptance: recover V4.23-level island recall on HSL, then evaluate HSL
packages, Page 23 and Adda against the protected checkpoint.
V4.28 is approved after intermediate checkpoint `99a9fa1`. It adds the sixth
typed graph relation, `context_reference_link`: a composite view may reference
multiple independently quoted products, but this relation is excluded from
proof components and can never merge them. For an authored sheet-level root
code such as N57, Detection may split products only with separate product
evidence; Naming retains N57 and adds deterministic A/B/C suffixes in product
order. The target is N57A kitchen, N57B island and N57C cabinet, not one
commercial N57 package.
V4.29 is the approved follow-up experiment. It preserves V4.28's proof rules,
context links, one Haiku call, temperature 0 and passive OCR recall aid, but
adds an exact-once package-decision ledger after the graph. Every commercial
visual group must resolve explicitly as `part_of_proven_component` or
`standalone_package`; a context-link source is shared Evidence rather than a
commercial group. A claimed but insufficient relation cannot silently suppress
a package. Runtime verifies every decision against the accepted proof
components and persists it with the Registry audit. Acceptance: HSL succeeds
without an unproved merge, every eligible group is accounted for, and the
result is then regressed against Page 23 and Adda before any checkpoint.
V4.29 is rejected by its first HSL run, not for an inference defect: the
full 31-row ledger exhausted Anthropic's 8,192 output-token limit and truncated
JSON (`stop_reason=max_tokens`). V4.30 retains the binary outcome but transmits
only the sorted `standalone_package_group_ids`; graph connectivity deterministically
establishes the complementary proven-component outcome and runtime persists the
complete per-group ledger. This removes duplicate output without raising the
model budget, adding a call, or relaxing proof validation. The same HSL, Page
23 and Adda acceptance gates apply.
V4.31 object-plan/context-link expansion is rejected as inconclusive. Its first
HSL run reached the Registry provider but exhausted the fixed 8,192 output-token
budget and returned truncated JSON before any semantic Registry validation. The
active behaviour is restored exactly to V4.30. A privacy-safe failed-JSON
observer now persists no raw response, only the reached top-level section,
terminal property key and depth, per-section observed character counts, JSON
error position, open-string state and output-budget utilisation. Its next run
must identify which contract section exhausted the budget before a new boundary
or output change is considered.
V4.32 is the approved one-call repair for the observed HSL self-edge failure,
where the model attempted `G4 -> G4` instead of relating the N56 plan to a
different N56 view or declaring it standalone. A proof edge now explicitly
requires two different group IDs. Before the existing compact singleton-ID
declaration, the same Registry response performs one final audit of every
unconnected object-evidence group against all other object-evidence groups:
add an accepted edge to a different group, otherwise declare the group
standalone. It adds no provider call, response field, token budget, router,
Sonnet path, or validation relaxation. The self-edge remains a hard runtime
rejection. Acceptance: valid HSL graph without a self-edge, then Page 23 and
Adda regressions before any checkpoint.
V4.33 adds the sixth typed graph fact, `dimension_equality`. It is distinct
from `dimension_transform`: it records the same readable physical dimension,
unit and scope on both groups without conversion or axis remapping. One equality
is strong support but cannot merge alone; two independent equalities are
sufficient dimension proof and further equalities reinforce that proof. Before
deciding every candidate relationship, the single Registry call now assesses all
six typed facts. It serializes every positive fact on accepted merge edges but
not a quadratic ledger of negative comparisons. This adds no provider call,
router, Sonnet path, output field, token budget or validation relaxation.
Acceptance: HSL must retain its visual-group inventory, emit the common N56
dimensions as typed facts, form only valid proof edges, then regress Page 23
and Adda before any checkpoint.
V4.34 replaces directional `context_reference_link` with an undirected
`reference_link` using lexically ordered `group_id_a` and `group_id_b`.
`shared_reference_group_ids` records a general view that relates two or more
independently quoted packages. It is shared Estimation Evidence, not a package
or a commercial owner. Reference links never merge components, and every other
object-evidence group remains either a proven merge component or an explicit
standalone package. This removes the artificial context-chain rejection without
relaxing merge proof or ownership validation. It adds no provider call, router
or Sonnet path. Acceptance: valid HSL graph with N76B, then regress Page 23
and Adda.
V4.35 keeps that undirected graph but validates `shared_reference_group_ids`
only after merge components and declared standalone packages are proven. A
shared composite view must directly reference at least two distinct commercial
package anchors, not merely two visual groups or two views of one package. A
generic floor plan or room layout remains `document_context`, even if it shows
placements, and can never become shared Evidence. This adds no model call,
router or Sonnet path. Acceptance: HSL must not classify G002 as commercial or
use G031-G033 as shared Evidence; N76B must instead be proven as its own
package, followed by Page 23 and Adda regression.
V4.37 removes the final duplicate package declaration from the one-call
Registry contract. Runtime derives singleton packages from the accepted proof
graph, so a model cannot fail the RFQ merely by omitting or miscopying the
same result into `standalone_package_group_ids`. Model `objects` rows become
optional descriptive metadata only. A graph component that lacks one valid row
is preserved as a deterministic quantity-one package, receives every physical
page containing its proven visual group as Estimation Evidence, and is marked
`review_required` in File Review. The Registry audit records accepted metadata,
discarded metadata rows, fallback object IDs and deterministic page supplements.
This adds no model call, router, Sonnet path or relaxation of proof, ownership,
classification or page-coverage validation. Acceptance: HSL must complete
without a descriptor/standalone-list validation failure, then regress Page 23
and Adda before checkpointing.
V4.38 replaces the sparse provider proof-edge response with a compact,
exact-once relation ledger. Every `object_evidence` pair has six persisted
criterion states: positive, checked-negative, conflict or unreadable. Every
visual group also returns its readable dimensions once. Positive graph facts
remain concrete and page-cited; two independently recorded dimension equalities
are sufficient merge evidence and three or more are very strong. Runtime builds
provisional components and packages only after the complete ledger, then applies
the semantic proof threshold. This keeps one Haiku call and temperature zero,
but raises the Registry output ceiling from 8,192 to 12,288 tokens to preserve
the complete compact ledger. Acceptance: HSL must return a complete pair ledger
without truncation, preserve every positive dimension fact in its merge graph,
and then pass Page 23 and Adda regressions. V4.39 retains every six-criterion
pair state and positive, page-cited dimension fact, but removes the duplicated
per-group `dimension_inventory` transcript from the model response. Full OCR
and rendered pages remain the literal source record for Estimation and graph
inspection. This corrects the contradictory instruction to both return and not
extract dimensions, while preserving the rule that Detection never infers or
publishes final external object dimensions. It keeps the 12,288-token ceiling
and one Haiku call. Acceptance: HSL returns valid JSON and its full graph,
then Page 23 and Adda retain their protected outcomes.
V4.40 is approved after the V4.38-V4.39 dense pair-ledger experiments proved
that a complete negative matrix cannot fit HSL within the established response
ceiling. It restores a sparse positive graph while retaining V4.33's six typed
facts, especially `dimension_equality`, and requires the model to inspect every
pair but serialize every positive equality, transform and other typed fact only.
`dimension_equality` records direct same-axis literal matches;
`dimension_transform` records a separately named unit or axis remapping. Both
may be present on one pair. Runtime derives components from accepted merge edges
only. A weak, cyclic, duplicate or otherwise unusable individual relation is
persisted as a rejected candidate and cannot fail the RFQ or erase unrelated
packages. Every unmerged object-evidence group becomes a quantity-one,
review-required standalone with its physical page Evidence. `reference_link`
is undirected, non-merging Evidence annotation: it adds linked pages to each
related package but cannot hide a standalone or block validation. Generic floor
plans remain `document_context`. This keeps one Haiku call, temperature zero,
full OCR and page Evidence, without Sonnet or retry calls. Acceptance: HSL
completes with every retained group assigned exactly once to a package, accepted
and rejected relations visible in the audit, and all positive equality and
transform facts persisted; then regress Page 23 and Adda before checkpointing.
V4.42 replaces the invalid V4.41 full pair ledger with the accepted V4.40
positive-fact graph. It keeps one Haiku call, temperature zero, full island
discovery, graph-derived packages, page Evidence and quantity-one standalone
fallbacks. Before the graph, the model records each retained group's literal
dimensions once in a linear source index. It then emits only positive typed
edges: `same_object_view`, `object_detail`, `reference_link`, or
`supporting_relation`. A supporting relation preserves one positive fact without
silently merging or sharing Evidence. Packages derive only from accepted merge
edges; every unmerged object-evidence group becomes review-required standalone.
An invalid dimension index is observable but cannot abort otherwise proven
packages. The HSL acceptance target is a completed File Review, every retained
group assigned once, N57 permitted as one source-root package for MVP, N76B
retained as its own dimensioned standalone when unconnected, and no quadratic
negative-pair output. Then regress Page 23 and Adda before checkpointing.
V4.43 retains one temperature-zero Haiku call and the V4.42 island and
classification stages, but removes model-owned graph, package, coverage and
metadata declarations. The model returns only complete visual islands,
per-island classification, and literal typed source dimensions without unit
conversion. Runtime checks every retained pair, records one exact equality as
support, accepts two independent matching overall dimensions or an independently
proven two-reading axis transform as a merge, and persists all resulting facts,
conflicts and graph audit. A single literal
`DRAWING NAME` code in an OCR title-block table may build a review-required
source-root tree for its sheet. It cannot override a direct same-kind overall
dimension conflict. Invalid model dimension inventory yields auditable,
quantity-one standalone packages rather than an RFQ failure. Generic plans,
title pages and title blocks remain out of Estimation Evidence. Acceptance:
HSL completes with N57 as an allowed whole source-root package and N76B
separate, then Page 23 and Adda retain their protected outcomes.

V4.44 is an approved isolated dimensions-only graph experiment. It preserves
the V4.43 visual-island and classification stages, one temperature-zero Haiku
call and full OCR Evidence, but replaces the provider's unbounded local-
dimension transcript with at most one maximal outer-envelope chain on each
readable horizontal and vertical axis. A direct outer total wins unless a
continuous outer segment chain sums to a greater span. Runtime alone sums
literal segments, compares all retained pairs, and writes only
`dimension_equality` facts. Equality permits up to one-percent drawing drift,
including 406 versus 407. The global document unit is read deterministically
from explicit OCR markers before Registry; bare values inherit it only when all
visible unit markers agree. No author-code root, transform, topology, conflict
or other relation type participates in this graph experiment. Acceptance:
inspect the HSL graph for maximal chains, computed sums and equality edges
before evaluating object packages, then decide whether this becomes the new
graph foundation or is reverted to V4.43.

V4.45 follows the failed HSL V4.44 run. It keeps the same one-call,
dimensions-only graph scope but makes the island to chain binding explicit:
one separately framed, dimensioned or positioned drawing is one immutable
visual group, even when it depicts the same product as its neighbour. The
model may return no chain for an unreadable axis. Runtime canonicalizes only a
completely empty synthetic chain to that existing no-chain state, preserving
all literal measurements. The graph remains only deterministic
`dimension_equality`; no packages, ownership, codes, transforms, topology or
other proof types are part of this experiment. HSL acceptance: the graph must
retain valid chains when another group has no readable outer size, and expose
the obvious external-width comparisons before any later object-assembly work.

V4.46 keeps V4.45's one OCR pass, one temperature-zero Registry call and
dimensions-only graph scope, but replaces each OCR image annotation's flat text
with structured literal geometry. Every image bbox now returns: the complete
verbatim text, `declared_dimensions` such as `H=60`, and one
`page_horizontal` plus one `page_vertical` outer-dimension observation. Each
axis explicitly states `readable` or `not_shown_or_unreadable`; no synthetic
blank chain is used. `H`, `W`, `D`, `L`, `Ø`, `R`, `T` and `THK` are literal
source symbols, not inferred object boundaries or chain segments. Detection
receives those facts separately, so `H=60` cannot be substituted for a nearby
literal chain segment. Acceptance: on HSL, page 4's `H=60` remains a declared
height fact while its horizontal `331 = 64 + 203 + 64` chain is independently
reported; measure the unchanged one-pass OCR timing before any Vision Object
Detection experiment.

V4.47 rejects V4.46's request that OCR infer horizontal or vertical geometry.
It restores the prior text-only bbox annotation and deterministically extracts
only exact symbolic literals from that transcription: `H=`, `W=`, `D=`, `L=`,
`T=`, `THK=`, `Ø` and `R`. The parser preserves page and source bbox, but does
not derive a chain, sum values, select an axis or attach a commercial object.
The Registry still owns all envelope-chain interpretation. Its diagnostics now
store a page-and-island comparison: model-attributed OCR literal IDs, literal
candidates on that page not attributed to the island, and the model's own
horizontal/vertical chains. Acceptance: HSL returns to the V4.45 OCR timing
range and island recall, while the audit exposes OCR and Registry dimensions
side by side before any graph or package change.

V4.48 is the approved native-PDF-text evidence experiment. It preserves the
single Mistral OCR pass, the V4.47 text-only annotation, temperature-zero
Registry, Visual Group discovery and dimensions-only graph scope. While Mistral
OCR reads rendered pages, runtime extracts authored PDF text spans with their
rendered-page coordinates. Deterministic code merges both literal sources into
one ordered OCR evidence package without resolving conflicts, inferring
geometry, creating object boundaries or changing the graph. Every text span
retains `native_pdf_text` or `mistral_ocr` provenance. Detection receives both
conflicting values and must visually resolve them. Scanned or raster-only PDFs
remain supported because an absent native layer is non-fatal. Acceptance: HSL
page 3 exposes the second elevation's `63, 61, 46, 47, 77, 64, 358` native
spans with page-pixel coordinates alongside the existing Mistral output, then
run the existing HSL Detection benchmark before changing any graph rule.

PENDING, P1, USER REQUEST, Detection island-view typology: after the current
outer-dimension extraction experiment is verified, add a separate, evidence-only
classification for common fabrication depictions. An elevation, front, end or
section view should expose width plus height; a plan/top view should expose
width plus depth. This is not permission to infer a missing measurement or a
commercial-object boundary. Define the types and their observable criteria,
then validate them independently against HSL, Page 23 and Adda before allowing
them to affect equality or later object assembly.

PENDING, P1, USER REQUEST, Detection Registry output and latency optimisation:
after the commercial-boundary experiment reaches a valid HSL graph, remove only
proven duplicated model output while preserving all inspectable typed facts and
the complete Estimation Evidence handoff. Prioritise code-derived explanations
from proof facts, deterministic page coverage from accepted groups and context
links, and compact typed classification bases. Do not shorten visual-island
descriptions or proof observations merely to reduce tokens. Measure input and
output tokens, first-token and total generation time, price and HSL/Page 23/Adda
regression behaviour before accepting it. Output reduction is a latency goal as
well as a cost goal; it must not add a model call or weaken validation.


PENDING, P1, USER OBSERVATION, stale Processing cycle after New Estimate:
investigate the authenticated-browser sequence in which a prior saved estimate
is still visible, the user starts New Estimate, and Processing remains on an
old cycle until refresh. Do not attribute this to OCR or Detection without
evidence. Reproduce against the deployed version and distinguish a stale
browser/session or route state from a genuinely active processing run. The
acceptance condition is that an old estimate cannot be presented as the active
new cycle, and a failed or abandoned cycle gives an explicit recoverable state.

DEFERRED, P1, USER DECISION, Detection external envelope dimensions: do not
make W/D/H extraction a Detection critical-path objective or an Estimation
precondition. Show only directly evidenced values as optional File Review
context and preserve unknown values otherwise. Trigger: a future dedicated
object-view and dimension-chain evidence architecture, approved separately.
The 04.10 original-OCR projection experiment is not a candidate implementation:
the current direct-PDF OCR result has no object-local drawing text to project,
the private evidence bucket accepts images rather than JSON, and the worker was
reverted. Before reopening, approve the object-local OCR evidence contract,
storage format and single-pass OCR profile, then test it without altering
Detection, quantity, deferred Naming or Preview publication.

DEFERRED, P2, USER REQUEST, Legal template research: review
https://github.com/General-Legal/legal-templates/ and identify reusable clauses,
document structures, drafting patterns, or process safeguards for Costerly's
future legal work. Recommend only evidence-backed adaptations that fit the
existing Terms, Privacy, Customer Content, and consent-release model. Do not
copy or implement templates automatically, and do not reopen the closed 3.11.1
legal release. Trigger: owner explicitly starts a new legal work block.

COMPLETED AND OWNER-ACCEPTED, 3.16.1 Partners workspace foundation: Partner is the required top-level entity.
Organizations use one company-scoped identity with Partner and Client roles;
one organization may hold both roles. A Project belongs to one Partner and may
reference one Client. Finalized estimates become immutable Project Versions.
The production interface is one Partners page with shared header navigation,
native expandable Partner rows, and nested Project rows showing Project,
Client, calculation date/time, total, and PDF. The current-page Projects action
is omitted. No Partner, Project, or Version detail routes belong in this stage.
Permanent records are not created before Final Approval.

COMPLETED AND OWNER-ACCEPTED, 3.16.2 Final Approval: replace Generate Proposal with one Final
Approval action available only after every object is priced and approved. The
action atomically matches or creates Partner and optional Client roles, matches
or creates the Project, assigns the next version number, and stores an immutable
JSON snapshot of Objects, project costs, and totals. Repeated approval of the
same estimate is idempotent. Final Approval remains on Objects and changes to a
pale green Approved state.

PENDING, 3.16.3 Processing handoff polish: after the current File Review
transition regression is removed, evaluate holding the completed Processing
screen slightly longer so the next fully styled File Review replaces it in one
perceived frame. Measure the existing Detection completion, server render,
target visible, and target styled boundaries first. Do not add a fixed delay
unless it improves the real production transition without increasing total
time unnecessarily.

COMPLETED AND OWNER-ACCEPTED, 3.16.4 Client Proposal PDF: Final Approval generates a private PDF from
the immutable approved snapshot. The header uses only populated Company
Contacts and the company logo. The commercial body contains Project, Partner,
optional Client, Objects with quantity and sale prices, Delivery, Installation,
VAT, and totals, with no self cost. Partners exposes the latest proposal through
a short-lived signed PDF link. The private production bucket was provisioned
and its upload, signed URL, and cleanup cycle verified. Remaining: authenticated
production acceptance of Final Approval and PDF download.
The owner refined the completion flow: Final Approval remains on Objects,
changes to an Approved state, and reveals a download row below Installation.
That row contains Client Proposal / Download PDF and Project Summary / Download
XLS. XLS remains disabled until the later consolidated project materials export
is implemented. The Partners header keeps shared navigation but omits the
current-page Projects action.
The approved Objects layout stacks each download action below its title. Client
Proposal stays in the first Objects column; Project Summary starts exactly at
the Installation input axis. The duplicate Project Summary label in the totals
footer is removed, and the Approved action uses a pale green completed state.
Project Price shares the exact Project Summary axis, Project Total retains the
rightmost axis, and VAT occupies the column between them.
VAT is centered between the unchanged Project Price and Project Total grid
lines. Proposal downloads use Project_Partner_YYYY-MM-DD.pdf as the external
filename while private storage paths remain immutable internal identifiers.

PENDING, 3.16.5 Project Summary XLS: generate a project-wide purchasing list
containing all materials assigned across approved Objects. The disabled
Project Summary / Download XLS control is the reserved UI entry point. Define
aggregation, duplicate-material merging, units, quantities, source prices, and
supplier fields before implementation.

DEFERRED, P1, USER REQUEST, 3.16.6 Unknown Partner completion path: a missing,
blank, or explicitly `unknown` Partner must never block Final Approval. Final
Approval must complete normally and store the finalized Project Version under
one company-scoped reserved Unknown Partner group in Partners. All unresolved
projects share that group until the user assigns a real Partner name. Renaming
or assigning the Partner must move the project to the matching real Partner
without changing its immutable estimate versions, proposal files, totals, or
approval history. Trigger: resume Projects and Final Approval completion work.

COMPLETED, OWNER-ACCEPTED, P0, USER REQUEST, 3.16.7 Price Lists rebuild:
replace the legacy
material-only Price Source flow with a source-first tool that keeps materials,
Material Jobs, excluded consumables, supplier identity, VAT,
review, and durable extraction state distinct. Stage 1 is the additive data
contract: retain source supplier spelling and aliases, link an operation-service
row to the existing global `reference_operations` catalog, and persist private
supplier operation offers separately from material offers. No existing source
or material offer is reclassified automatically. Detailed contract:
`notes/PRICE_LISTS_REBUILD_3_16_7.md`. The 2026-10-07 closure contract makes
supplier resolution, material and offer merging, VAT evidence, source lifecycle,
final-cycle UI, permanent deletion, and minimal Needs Review the P0 completion
scope. Owner accepted the ordinary-source extraction path on 2026-10-09.
Supported JPEG, PNG, PDF and mixed batches retain independent source handling
and merge only on the canonical supplier plus invoice identity. Price and Unit
are the only Review reasons. The scanned multi-invoice-PDF router remains
explicitly deferred in `notes/PRICE_LISTS_CHECKPOINT_3_16_7_2026_10_08.md`.
A later Estimation resolver consumes accepted offers only and is not a reason
to reopen frozen supplier ingestion behavior.

ACTIVE, P0, USER REQUEST, 3.17.1 Unified material taxonomy, identity, brands,
and Supplier Operations: establish one bilingual, structured normalisation contract
for Price Source, company catalog, Israel Price List, Detection and Supplier
Operations. Canonical display order is entity, primary attribute, brand, then ordered
secondary attributes. Supplier SKU remains supplier-scoped evidence only. The
work includes Hebrew/English aliases, OCR-tolerant variants, department-scoped
brand aliases and a Supplier Operation route to reference operation plus supplier
operation offer, never a material offer. It must preserve the frozen 3.16.7
supplier, VAT, source lifecycle and UI paths. Contract:
`notes/MATERIAL_TAXONOMY_3_17_1.md`.
Owner accepted the five production departments (Wood, Metal, Glass & Plastics,
Stone, Coating), distinct entity roles, and multi-department affinity for
Hardware and Consumables. 3.17.1.3 is active: complete the Material Family
Matrix, including primary and secondary attributes, family-scoped brands, and
eligible operations. Thickness and other identity attributes do not alter
operation eligibility; no operation is mandatory. Contract:
`notes/MATERIAL_FAMILY_MATRIX_3_17_1.md`.
Owner accepted the Company Price Catalog structure on 2026-10-11: its six
top-level sections are Wood, Metal, Glass & Plastics, Stone, Coating and
Hardware. Hardware is a catalog section, not a production department, and no
longer maps to Wood. Keep Consumables excluded from company-catalog persistence
and preliminary-estimate selection. Rename the existing Material Jobs UI to
Supplier Operations.
Material Family Matrix and staged Operation Dictionary accepted by owner on
2026-10-10. The next gate is source-backed time priors and formula parameters
by recipe, beginning with panel-saw and CNC-router sessions. Shared setup and
cleanup apply only within one compatible route and machine session, never
across different machines. Contract:
`notes/OPERATION_DICTIONARY_3_17_1.md`.
Existing Labor evidence has been recovered for this gate: source audit,
baseline, Furniture Core recipes/formulas and route catalog. It must be
reclassified before use because the current engine has 53 flat v0 baselines,
while the broader library mixes source-backed, equipment-bound and derived
priors.
Owner accepted the deliberately incomplete Operation Dictionary v1 on
2026-10-10. Missing operations remain a controlled gap list for a later
versioned expansion. They must not be folded into a similar operation or given
an invented time value.
Owner confirmed the approved new semantics for Hardware, Consumables and
Packaging on 2026-10-10. They will be rebuilt as entity roles in the new
canonical catalog model: Hardware and Consumables have one or more
production-department affinities for retrieval/context only; Packaging has no
production department. The owner also authorised a direct rebuild rather than
legacy product compatibility because the current catalog is transitional and
unused. Internal readers still require complete replacement and verification.
Architecture checkpoint:
`notes/CATALOG_ARCHITECTURE_MIGRATION_3_17_1.md`.
Terminology accepted on 2026-10-10: `Material Resolver` resolves canonical
material identity, `Material Engine` calculates purchasable quantities, `Labor
Resolver` resolves selected operations to route/recipe/machinery session, and
`Labor Engine` calculates staged labor. Sheet-material quantity is nesting and
whole-purchase-unit rounding at project scope, not a generic waste percentage;
V1 does not credit offcuts across projects. Material identity, material supply,
Price Source and labor review states remain separate.
P0, USER REQUEST, 3.17.1 catalog-gap provisional estimate and Staff review
inbox: every review state must still produce an explicitly provisional estimate
rather than block calculation. A bounded research pass may propose a material,
source price, operation or route with provenance, confidence and assumptions.
It is stored only inside that estimate, never as a candidate or provisional
catalog row. Each gap creates a deduplicated internal review job carrying the
source evidence, case-local assumption, calculation trace, gap type and
reoccurrence count. A staff reviewer later creates the authoritative catalog
record separately, if justified. Build the data contract, job lifecycle and
Staff Admin review interface after owner approval of the fallback policy.
Implementation started on 2026-10-11 from checkpoint
`notes/CATALOG_REBUILD_CHECKPOINT_3_17_1_2026_10_11.md`. Increment 1 adds
only the catalog-V2, case-local-assumption and Catalog-Gap-Job contracts in
`db/sql/2026_10_11_catalog_v2_contract_foundation.sql`; it does not apply the
migration, switch readers, write research into canonical catalog rows or expose
the Staff Admin Inbox. Contract: `notes/PROVISIONAL_ESTIMATE_CONTRACT_3_17_1.md`.

Decision correction, 2026-10-13, Material defaults versus assumptions: a
Family Default is not an assumption and never alters OCR evidence. It may fill
only a missing Pricing Key fact after the material family itself is proven,
then continues through the normal Company-first, Israel-second Resolver path.
Its trace records each policy-applied value. A missing family is not eligible
for a Family Default. A deterministic construction rule may make a
case-local `material_family_assumption` from object type and part role, for
example a kitchen-cabinet carcass to melamine-faced particleboard; it remains
review-visible because the input did not prove that family, but it is not a
Catalog Gap. A complete uncommon specification with no Company or Israel
candidate is the separate `catalog_gap_assumption` path and creates the
deduplicated Catalog Gap Ticket. Initial Family Default values require an
owner-approved, versioned baseline matrix rather than implicit selection from
whatever prices happen to exist.

Implementation increment, 2026-10-13, 3.17.4.1: `reference_material_family_default_variants`
stores ordered default variants anchored to an active Israel pricing identity.
The V3 Material Engine applies a variant only to a proven family with missing
facts, verifies that anchor still has an active material-only Israel price,
and persists the applied values in the Material Plan trace. The initial matrix
contains raw MDF 17 mm and raw plywood 17 mm because each has a live Israel
candidate. LDSP 15/17 cannot be activated yet: the active Israel Reference has
no corresponding price identity, which is a catalog-enrichment task rather
than a reason to invent an anchor. Missing-family construction assumptions are
not part of this increment.

Reader/UI scope is mandatory, not a later cosmetic pass: migrate Price Source
ingestion and review/list behaviour, Company Catalog, Estimation/Object Detail
and Staff Admin to the same V2 taxonomy contract. Preserve the accepted Price
Source rule that departments/families without an eligible material row are not
rendered. A Stone row appears after it is standardised into an active Company
Price Catalog offer; a future Israel Catalog link or curation signal never
blocks that publication.
The approved Price Source migration sequence and protected behaviour are in
`notes/PRICE_SOURCE_V2_UPDATE_PLAN_3_17_1.md`.
P0, COMPLETED, 3.17.2.1 Global-Market catalog contract and deterministic
migration plan: owner approved the full
international architecture on 2026-10-11. The canonical chain is Global
Catalog -> Market Catalog (Israel first) -> Company Price Catalog. Checkpoint,
production evidence inventory, mapping rules and cutover gates are in
`notes/GLOBAL_MARKET_CATALOG_CHECKPOINT_3_17_2_2026_10_11.md`. This task
reconciled the unapplied V2 contract with that chain and created an executable
deterministic migration plan before any production SQL application, reader
cutover or legacy-data deletion.
P0, COMPLETED, 3.17.2.2 Global family registry seed: created the approved Global
family vocabulary, primary and secondary attribute contracts and possible
operation eligibility only. The seed must not import legacy rows, construct an
Israel listing, write a Company offer or change a reader. `stone_edge_profiling`
remains excluded until its separate operation and Labor baseline are approved.
P0, COMPLETED, 3.17.2.3 Israel-market projection and strict backfill:
only a row with a proven approved family and that family's required primary
attribute may create a Global model and Israel variant. The 2026-10-11
production dry-run permitted and production backfill created 3,793 active
Global-model and Israel-listing records, excluded 247 consumables by policy,
and retained 408 review rows. No missing thickness, diameter or other primary
attribute was invented to improve this coverage.
P0, COMPLETED, 3.17.2.4 Material Resolver V2 identity bridge: the Estimation
publisher now reads active V2 Global models, Israel market listings and their
approved legacy mappings. It enriches only the 3,793 mapped legacy rows with
their V2 identity, while retaining all 4,448 legacy rows in the resolver
index. The 247 policy-excluded and 408 review-required rows therefore remain
available as fallback evidence and cannot make an estimate disappear. Legacy
material IDs remain the temporary price-identity bridge until the pricing
catalog and Company Price Catalog are migrated to V2 links.
P0, COMPLETED, 3.17.2.5 Company Price Catalog V2 forward bridge: a
Price Source row that has already proved its legacy reference-material identity
now projects deterministically to its Israel Market Listing. The projection
preserves staff-reviewed mappings, records bridge evidence, and cannot fail or
invalidate the frozen Price Source identity flow. The current catalog has 29
items but no proven reference-material links, so no historical item was
guessed or backfilled from its name, price or supplier SKU.
P0, COMPLETED, 3.17.2.6 Source Agent taxonomy adapter and Price Source sections:
Source intake now recognises Stone families and emits V2 family/role/production
department evidence for every deterministic taxonomy match. Hardware is a
standalone Company Price Catalog section, never a Wood row. Price Source now
renders the approved six sections, Wood, Metal, Glass & Plastics, Stone,
Coating and Hardware, and Material Jobs is named Supplier Operations. The
adapter is evidence-only: it must not auto-create a Global model, Israel
listing or Company offer when no proven catalog link exists.
Stone design coverage is complete for current kitchen and furniture scope:
natural, engineered, sintered, porcelain/ceramic, solid-surface and terrazzo
families, countertop-like uses, brands, attributes and possible operations are
defined. The subsequent implementation must create the approved
`stone_edge_profiling` operation only together with its route, driver schema
and Labor baseline. It must not be added as an unpriced catalog label.

ACTIVE, P0, USER REQUEST, 3.17.2.7 Hardware brand and Product System registry:
move the 15 curated Hardware manufacturers from the Source Agent-only vocabulary
into the V2 Global registry, with family-scoped brand aliases and a catalogued
Product System layer. Source evidence may recognise an exact system such as
Blum MOVENTO only after the Hardware family is independently established. A
recognised system may supply the known manufacturer; neither it nor any raw
supplier SKU may invent a nominal length, load class or Global model variant.
Seed only manufacturer-published systems, not every SKU or price offer. The
first scope covers drawer slides and systems, lift/flap mechanisms, door
systems, storage systems, connector systems and hinge systems where the brand
publishes a distinct named line. Product variants and supplier-SKU-to-variant
crosswalks remain staff-authoritative later work. In the same pass, audit
Source Agent static registries against V2 and record unmigrated vocabulary;
do not silently treat it as V2 data.

ACTIVE, P0, USER REQUEST, 3.17.2.10 Estimate Ready Material Resolver:
the Material Pricing Key registry is applied for all 54 active Material Family.
Blue and Green are Estimate Ready: both have a complete Pricing Key, required
purchase format, valid active price and estimation unit; Green also has an
Israel canonical link. Yellow lacks a Pricing Key or required purchase format,
and Red lacks family identity. Complete offer-level purchase format, Source
normalisation and Price Source display, then make Blue and Green eligible for
deterministic selection. The future Material Engine selects minimum total
purchasable cost at document scope, not merely the cheapest unit price.
Contract: `notes/MATERIAL_RESOLVER_SELECTION_POLICY_3_17_2_9.md`.
Current stage: broaden the Global family supply-format registry from verified
Israeli and manufacturer catalogues, normalise ft/cm/mm source notation, and
complete a one-sided format only where exactly one active candidate matches.
The owner must apply `2026_10_12_correct_company_offer_formats.sql` before
this stage can be deployed or tested in Price Source.
Implementation state, 2026-10-12: Resolver and the Price Source indicator
now derive Estimate Ready from the active Global Pricing Key policy and the
specific supplier offer's purchase format. Blue and Green are eligible;
Yellow and Red remain excluded. Pending production verification with a fresh
source cycle. Multi-candidate total-purchasable-cost selection remains the
subsequent Material Engine scope.

Implementation update, 2026-10-13: every source route now converges through
the same Family-first deterministic normalization contract after extraction.
Structured XLS/XLSX columns enrich literal source evidence without replacing
the raw supplier description. The contract extracts only the proven Pricing
Key facts for its Family, including profile section/wall, stone type,
coating system and sheet dimensions. The Global pricing-identity generator
now projects only policy-complete existing materials into V2 classes and does
not invent a missing key or price. Its read-only production dry-run found 364
policy-complete classes from 4,515 Global materials, with active source model
prices for 300. The next fresh-source verification intentionally ignores
legacy Company Catalog rows that the owner will delete before re-import.

Production benchmark, 2026-10-13: a clean import of the controlled legacy XLS
now has 37 active material offers: 18 Green, 19 Blue, 0 Yellow and 0 Red.
The immutable input hash, import result, scope boundary and comparison rule
are recorded in
`notes/PRICE_SOURCE_RESOLVER_BENCHMARK_3_17_2_10_2026_10_13.md`. Do not
compare it to the older 43-offer snapshot, which included six pre-existing
catalog offers.

ACTIVE, P0, USER REQUEST, 3.17.3.1 Material Engine deterministic core:
introduce the calculation-local Material Demand and Material Supply Candidate
contracts, then build and test estimate-wide purchase planning. The Engine must
consolidate only Resolver-compatible demands and select the least-cost complete
basket, not a per-unit-price winner. Scope covers rectangular sheet nesting
with explicit kerf, linear-stock packing, piece-package rounding, direct-unit
purchase and demand-to-purchase traceability. It must not alter the Estimation
Agent, live Estimate publisher, Labor Resolver or catalog data in this task.
The subsequent integration task must extend the agent contract with
calculation-local part geometry and connect Engine candidates directly to the
project-level material-plan path.

ACTIVE, P0, USER-APPROVED, 3.17.3.6 Drawer-slide 400 mm last-resort default:
the prior derived-length rule is cancelled. Estimation V3 retains only
evidenced facts. When an otherwise unresolved `hardware_drawer_slide` lacks
an explicit depth, Material Engine deterministically supplies `400 mm`, then
uses the ordinary Company-first, Israel-Reference-second resolver path. The
400-mm value is a runtime last-resort policy, not a source fact or catalog
default variant, and must be persisted in the plan trace. Explicit source
depth always wins.

ACTIVE, P0, USER-APPROVED, 3.17.3.7 Catalog-driven Material pipeline audit:
verify the one shared Family, Pricing Key, alias and purchase-format contract
for every active Family, rather than a hand-picked material fixture. The
read-only audit must expose unsupported V3 Pricing-Key fields, Price Source or
Estimation alias gaps, and Israel Reference positions that cannot become
Resolver candidates. It must not create a new material model, write Catalog
data, select a price, or treat catalog gaps as assumptions.

ACTIVE, P0, USER-APPROVED, 3.17.3.8 Resolver eligibility closure: close the
catalog-driven audit gaps Family by Family. Owner-approved first rule: every
active `acrylic_pmma` Israel listing receives the `2400 x 1220 mm` catalog
default purchase format. `packaging_material`, `paint_lacquer_stain`,
`powder_coating`, `primer`, and `filler_hardener_thinner` are deterministic
formula-overhead scope, not Resolver Material Demands. Do not silently remove
their cost from runtime before formula rows are connected.

ACTIVE, P0, USER REQUEST, 3.17.3.2 Calculation-local part geometry and
shadow planning: extend the compact Estimation facts transport with rectangular
parts linked to material requirements, full geometry, quantity and rotation
permission. These parts remain inside one estimate and never become Global
catalog entities. Version the page Facts Agent to invalidate its own stale
cache. Feed the new Material Engine as a document-wide read-only plan until
project-level material-plan persistence and rendering are connected.

Implementation stage, 2026-10-13, 3.17.3.3: Resolver-cleared Company offers
now bridge to physical Material Engine candidates in a non-blocking
document-wide shadow plan. The bridge preserves offer-level purchase format,
converts source prices to ex-VAT physical purchase-unit price, and groups only
the active family Pricing Key. The runtime returns only shadow diagnostics;
the live publisher still owns displayed per-object material lines. Israel
Reference candidate conversion remains before direct project-level material
plan output. Accepted fallback chain: complete Company
basket, otherwise complete Israel Reference basket, otherwise an
estimate-local, review-required assumption. The assumption records why it was
needed and never writes back to either catalog. Catalog V2 already has the
target persistence contract: case-local assumption, deduplicated staff-only
Catalog Gap Ticket and occurrence. Runtime creation, Staff Admin review UI and
authoritative catalog-resolution workflow remain unimplemented follow-up work.
Name accepted: `Assumption Fallback`. It is a separate Estimate-orchestration
service after Material Engine, not an Estimation Agent or Engine subsystem.
Build it after Company and Israel candidate planning is accepted and the
Material Engine produces the project-level material plan; it must consume an
Engine-produced `assumption_required` outcome rather than re-run material
selection itself.

Implementation stage, 2026-10-13, 3.17.3.4: Israel Reference is now in the
same Material Engine candidate bridge. An active IL pricing identity must match
the exact completed Family Pricing Key, have an active material-only ILS price,
and have a compatible physical supply format. Square-metre prices become real
sheet candidates through documented family formats, linear prices become stock
candidates, and discrete prices become package candidates. A price per sheet
is intentionally not copied onto every generic family format. The Engine uses
a complete Company basket first, then a complete Israel basket, otherwise
returns `assumption_required`. This stage does not compare against, or depend
on, any former estimator. Project-level plan persistence, rendering and the
separate Assumption Fallback service remain the next work.

Implementation stage, 2026-10-13, 3.17.3.5: an estimate now persists one
derived, estimate-wide Material Plan and a user may override only the net
material norm for one finished item. The Engine recomputes Company-first and
then Israel-Reference purchase candidates after every norm or object-quantity
change. It performs sheet nesting, stock and package rounding at estimate
scope, persists the complete purchase trace, and allocates the resulting
purchase cost back to Object Detail material rows by physical demand. The
allocated Object Detail material costs sum exactly to the rounded plan cost.
Manual area norms never claim fragmented offcuts as usable geometry. Any
material-input change marks the plan stale, clears all object approvals and
coalesces a full recalculation, including a guaranteed follow-up run when an
edit lands during an active rebuild. Final Approval remains blocked until the
plan is `planned`. Schema was applied through
`2026_10_13_estimate_material_plan_v1.sql`; automated verification covers
sheet, stock, package, manual-norm, allocation and approval-gate paths.
Production acceptance still requires a multi-object estimate to verify that
the visible object costs sum to the read-only estimate-wide purchase plan.
The next Material Engine task is read-only Purchase Plan presentation,
including stock format, purchased quantity, remaining material and allocation
trace. Assumption Fallback remains a separate orchestration task.

ACTIVE, P0, USER REQUEST, 3.17.4.1 Estimation Agent V3 material-only cutover:
replace the active Estimation path with a standalone V3 material-facts contract,
Material Resolver and estimate-wide Material Engine integration. V3 must not
import, invoke or publish V2. Labor, manufacturing and overhead remain
disabled until their own engines are accepted. Company-first and Israel
Reference candidate selection remain deterministic. When neither supplies a
complete candidate set, V3 records `assumption_required` without inventing a
price. V2 is retained only as isolated legacy history pending an explicit
destructive removal task. Acceptance: active runtime and UI read V3 facts,
publish only material norms, persist the project-level Material Plan, and do
not contain an active V2 dependency.

Checkpoint, 2026-10-15: the active end-to-end path now persists and renders a
partial V3 Material Plan. Resolved allocations publish the exact selected
canonical Company Catalog or Israel Reference name and allocated cost while
the overall plan remains `needs_review`; unresolved lines remain unpriced.
The first live run is not accepted as a correct estimate. It exposed
unsupported inferred MDF parts, a 14.25 m envelope proxy in place of the
explicit 4.130 m track, unsupported Oak/30-mm timber selection, and a
sliding-door requirement incorrectly selecting `Folding door system`.
Continue this same task with evidence-bound facts: prohibit invented part
rectangles, prefer exact measurements, make any proxy explicit and
review-visible, and guard physical subtype compatibility before selection.
The complete evidence and commit checkpoint is
`notes/ESTIMATION_V3_MATERIAL_PIPELINE_CHECKPOINT_2026_10_15.md`.

Israel Reference rebuild, points 1-2, 2026-10-14: the earlier Coverage Audit
incorrectly treated the legacy `reference_material_pricing_identities` bridge
as the Israel catalog. It is superseded. `tools/audit_israel_reference_catalog.py`
now reads the actual canonical chain: Family -> Global Model -> Israel Listing
-> Israel Price and Purchase Format. A Company row maps many-to-one to an
Israel Listing by Family and Pricing Key. Secondary fields never create a new
price class. The corrected snapshot has 54 active families: 18 lack a
canonical model, 19 have a canonical priced position but no purchase format,
six hardware families have no active package price, and five contain models
without their required Pricing Key. It also exposed incorrect backfill data,
including Plywood-named rows assigned to the MDF family. Do not seed further
defaults or prices until the owner and team have reviewed the catalog-layer
contract and the bad family assignments. Hardware package selection remains a
separate deterministic Company-first, Israel-second branch.

ACTIVE, owner-approved, 2026-10-14, Israel Reference normalization: convert
the actual Israel catalog chain into usable resolver data. Every active
listing must have one Family, a complete Pricing Key, an active Israel price
row and, where its Family requires it, an approved purchase format. Every
Family must have one active default listing only when that listing already
has an active Israel price. Do not fabricate a source price. The first
migration is `db/sql/2026_10_14_normalize_israel_reference_foundation.sql`:
it removes wall thickness from furniture-profile Pricing Keys, corrects the
three Plywood rows wrongly placed in MDF, and separates explicit hardware
names from the generic furniture-system Family while preserving their legacy
source and price anchors. The next migration must cover remaining broad
Family splits, default listings and supply formats, followed by the existing
read-only catalog audit.

Material-fact boundary correction, 2026-10-13: V3 must establish only
material family, proven Pricing Key facts and evidenced part geometry. It must
not guess a unit or a purchasable format. A directly evidenced discrete count
may remain in facts, but is not a purchase quantity. The Resolver
selects a compatible Company or Israel candidate first. The Material Engine
then derives the Object Detail net norm from candidate form plus allocations:
sheet allocations render as square metres, linear stock as metres and discrete
stock as pieces. A material with no evidenced usable geometry may remain
identified, but remains review-required and unpriced instead of receiving a
fictional `1 piece` demand. The V3 facts-agent cache version is bumped so the
old guessed-unit facts cannot enter a new plan. Pending production acceptance:
rerun the same three-object document and verify that a resolved part-backed
material receives a deterministic unit and norm, while an unresolved profile
does not receive a cost or unlock approval.

Pricing Key extraction correction, 2026-10-13: V3 now receives the required
evidence-field names from the active Pricing Key registry for every allowed
Resolver family. It searches source evidence for those facts, but Resolver
remains the only authority that decides whether they form a completed key.
This allows the prompt to actively seek, for example, MDF thickness and tube
metal, section and wall thickness without turning absent evidence into a
model-generated specification. Cache version `estimation_material_facts_v3_2`
separates these facts from prior runs.

Multilingual intake grammar correction, 2026-10-14: each active Global
Catalog family has an explicit English, Russian and Hebrew alias set, and each
Pricing Key fact has the corresponding field labels. V3 receives only the
aliases and fact labels relevant to its currently allowed Resolver families.
They guide family and attribute recognition, but cannot prove a missing number,
select a purchasable offer or create a catalog link. Exact aliases are unique
across families. The standalone source-taxonomy product-system lookup is also
kept on the same canonical Global-family projection, so Hardware rows cannot
fail before taxonomy is established.

COMPLETED, P0, USER ACCEPTED, 3.17.1.4 Shared aliases for incoming material text:
move every Family alias, Pricing Key label/value alias, brand alias and unit
alias out of runtime dictionaries into the catalog. Both Estimation and Price
Source must read the same active rows. An alias may establish only a Family,
Pricing Key fact, brand or unit. It never selects a price, purchase format,
Company Catalog offer or Israel Reference Position. Exact aliases for a known
Israel Reference Position remain a separate later mapping, after Family and
Pricing Key are proven. Initial implementation adds the protected tables and
the seed from the former Estimation registry in
`db/sql/2026_10_14_shared_material_aliases.sql` and
`db/sql/2026_10_14_shared_material_aliases_seed.sql`, plus the existing
non-Hardware Price Source brand inventory in
`db/sql/2026_10_14_shared_brand_aliases_seed.sql`. Estimation V3 now reads
only the new persistent rows. Price Source reads the same persistent rows for
Family, Pricing Key, brand and unit interpretation. No local synonym fallback
is permitted after cutover.

Accepted 2026-10-14: live catalog audit confirms 54 multilingual Families,
845 Family aliases, 411 Pricing Key labels, 268 Pricing Key value aliases,
162 unit aliases, 264 brand aliases and 379 product-system aliases. Every
live Family has EN/HE/RU coverage; every multi-Family spelling is explicitly
ambiguous, with no unapproved collision. Estimation V3 and Price Source both
read this shared catalog. Deployment and a production end-to-end check remain
a separate release checkpoint, not unfinished alias-catalog work.

Furniture metal-profile policy correction, 2026-10-13: wall thickness is not
a Pricing Key fact for `metal_tube` or `metal_profile_angle_channel`. An
unstated furniture-profile wall uses the manufacturing default of 1.5 mm;
an explicit wall remains secondary source provenance. `metal_flat_bar` is
deliberately excluded because its thickness is a physical cross-section fact
and can affect price. The corrective SQL is
`2026_10_13_furniture_profile_wall_thickness_default.sql`. MDF 20 mm and
perforated steel sheet 5 mm are confirmed catalog gaps, not extraction gaps:
each still needs an authoritative active price and supply format before the
Resolver can yield a candidate.

Resolver correction, 2026-10-13: the first live multi-object Material Plan
proved that Object Facts had been given legacy Israel price classes rather
than the Resolver's purchasable-family vocabulary. That allowed an unsupported
fact such as `stainless_steel` to replace the proven form `metal tube`, so no
Pricing Key was built and neither Company nor Israel candidates were queried.
Facts now receive only active Family Pricing Policy vocabulary, accept
`metal_type` only as an explicit specification, and forbid invented alloy,
wall or grade facts. Global family codes without a source alias are valid
Resolver families. A 20 mm MDF requirement correctly remains a Catalog Gap
until an authoritative Company or Israel offer is added: current Company data
contains 18/19 mm only and current Israel Reference has no 20 mm MDF price.

V2 Family bridge removal, 2026-10-14: active taxonomy, Resolver, Material
Engine, V3 facts and Israel identity seeding use only current `family_code`
values. The former source-label projection, including mappings such as
`drawer slide` to `hardware_drawer_slide`, is removed rather than renamed.
The remaining test migration must replace old source-label expectations with
current Family codes; no product fallback may be restored to satisfy them.
Historical records with an old stored Family spelling require a one-time data
audit before their next Resolver run. Faced MDF 20 mm remains an explicit Catalog Gap and

Release audit update, 2026-10-14: the live catalog has 54 active Families,
845 Family aliases, 411 Pricing Key labels, 268 Pricing Key value aliases,
162 unit aliases, 264 brand aliases and 379 product-system aliases. Every
active Family has English, Hebrew and Russian coverage. The audit found 16
additional multi-Family spellings; the follow-up seed records each as
ambiguous with explicit candidate Families, so none is resolved by ordering.
incomplete facts remain review-required. A plan with any earlier Resolver gap
is always `needs_review`, even when other requirements already have concrete
purchase lines. Those partial lines remain traceable diagnostics but can never
unlock Final Approval.

Lighting-material request, 2026-10-14: lighting is not one generic Hardware
line. The catalog and Resolver need distinct purchasable families for LED
strip, aluminium LED profile with diffuser, LED power supply and lighting
connector/cable. Candidate Default Matrix baseline: an 8 W/m strip sold in
5 m coils and a 2 m profile with diffuser. Material Engine must group matching
lighting runs across the entire Estimate, round strip to 5 m coils and profile
to 2 m lengths, then derive compatible power-supply capacity from total
installed strip length and strip W/m. The configured power headroom, default
colour temperature and default profile form remain pending owner approval. A
user-specified voltage, colour temperature, strip power, profile form or
power-supply capacity always overrides the default and is retained as source
evidence.

DEFERRED, P1, USER REQUEST, Aluminium/PVC glazing and enclosure pilot:
prepare a separate catalog and Resolver program for the prospective aluminium
and glazing company pilot. Scope: aluminium square, rectangular and glazing
system profiles; thermal-break variants; glazing beads and gaskets; glass-unit
types; aluminium/PVC hybrid profiles; fasteners and accessories; supplier
lengths and compatible cut/waste rules. These are not generic furniture-metal
families. Their family taxonomy, Pricing Keys, aliases, default variants and
Material Engine purchase rules must be designed from the pilot supplier
catalogue and real glazing estimates. Do not make square or rectangular
aluminium glazing profiles a substitute for the existing carbon-steel square
and rectangular furniture profiles.

ACTIVE, P0, USER REQUEST, 3.17.2.11 Universal canonical material-name
contract: at source-row processing time, build every company-catalog display
name solely as `Entity -> one or two proven key attributes -> confirmed brand
when present -> ordered secondary attributes`. Raw supplier prose, SKU,
quantity, packaging wording and a candidate or uncertain brand must never
enter the canonical name. A physical offer format is a key attribute when
proven, rendered as a full `length x width mm` format or as its one proven
side only when completion is ambiguous. The same renderer must project
existing catalog offers without mutating immutable source evidence. Every
processed-material projection, including Catalog, Needs Review, Source Detail,
and later Object Detail material lines, must call this same renderer. The
second display line is literal `raw_description` evidence in the source script,
never a translation or model-normalized phrase. Acceptance:
the two latest plywood sources display their `3100 mm` distinction at once,
the fallback sheet format is visible where resolved, and unconfirmed brands do
not appear in any new canonical name. Add a deterministic multilingual
measurement-alias grammar before name rendering: thickness, length, width,
depth and diameter labels; metric, imperial and Hebrew units; sheet-format
labels; and source-safe separators. A bare number is accepted only in a
proven entity-adjacent or explicitly labelled measurement position, never as
SKU, quantity or packaging notation.

PENDING, P1, USER REQUEST, 3.17.2.12 Price Source upload resilience:
accept legacy XLS through a production-supported parser, while preserving XLSX,
CSV, PDF and image handling. Before that format support is released, an invalid
extension must be rejected at selection time and must keep Extract disabled;
server validation remains the backstop. Add a genuine Cancel extraction action:
it must signal the active worker, close the live provider stream, prevent any
post-cancel persistence and show a terminal Cancelled state. Do not implement a
cosmetic button that merely detaches the browser while work continues. Large
structured spreadsheets must be partitioned into bounded deterministic row
groups or otherwise avoid a single unbounded Claude response, rather than
raising the 60-second stream cap and making the owner wait longer. Acceptance:
the supplied legacy XLS and its XLSX equivalent both parse, a 44-row workbook
is split before model extraction, invalid files cannot start a cycle, and
Cancel reaches a terminal state without catalog/source persistence. Automated
verification passed in commit 40f4739; the 44-row XLSX production import and
resolver-status checkpoint are recorded in
`notes/PRICE_SOURCE_XLS_RESILIENCE_CHECKPOINT_3_17_2_12_2026_10_12.md`.
Production acceptance still requires one XLS import and one Cancel during
extraction.

Production correction, 2026-10-13: the XLS parser and uploader were already
released, but the existing private `company-price-sources` Storage bucket
still allowed XLSX only. Apply
`db/sql/2026_10_13_company_price_sources_legacy_xls.sql` before the legacy
XLS acceptance run. It preserves every enabled MIME type and adds only
`application/vnd.ms-excel`.

DEFERRED, P1, USER REQUEST, 3.17.2.8 Construction Scenario Library and Staff
Admin: define a controlled, versioned library of full estimating archetypes,
starting with kitchen modules and furniture. A scenario describes the complete
base composition, evidence-triggered branches such as doors, drawers, shelves,
lighting and significant hardware, material and labor requirements, plus a
low-impact allowance for cheap construction sundries. It is not a universal
furniture ontology and must never silently invent a supplier SKU, a price, a
labor route or a catalog record. The earlier narrow draft focused on legs and
wall suspension, and is explicitly superseded, see
`notes/CONSTRUCTION_PATTERN_LIBRARY_3_17_2_8.md`.

Create a staff-only Admin interface to list active and inactive patterns, read
their human-readable contract and machine rules, edit a draft, activate a
version, deactivate a version, and view where a version was used in estimates.
Every edit and activation requires an immutable version and audit history. The
interface must not expose source evidence to non-staff users and must not allow
an edited rule to rewrite a completed estimate. Dependency: approve the V2
data contract and deterministic Estimation use path before UI implementation.

ACTIVE, IMPLEMENTATION CHECKPOINT `5f6360f`, P0, 3.15.24 canonical object quantity and durable Object Detail route:
make item quantity editable on File Review, Objects, and Object Detail. All
three screens share `rfq_detected_objects.quantity` as the canonical record;
the estimate row is its synchronously updated workflow read model, avoiding an
extra detected-objects query on every screen render. A change must preserve unit
self cost, recalculate commercial line and project totals, clear that object's
approval, and become visible on every screen without rerunning Estimation.
Objects Review keeps the fast live-session bridge, but its normal link must use
the durable company-scoped object route token so an expired Streamlit session
restores Object Detail instead of falling through to Upload. Acceptance covers
edits from both new inputs, cross-screen persistence, reapproval behavior, and
the expired-session Review scenario in authenticated production.
Object Detail follows its existing approval boundary: table edits and item
quantity remain a page-local draft until Approve Estimate persists one snapshot.
Back to Objects must ask before discarding a changed draft. Objects quantity is
an independent immediate-save field. Both quantity controls clear their current
value on focus so the first typed digit replaces, rather than appends to, the
displayed value. The Objects quantity input shares the Sale price input axis.
The native browser confirmation is not accepted UI. Use the Costerly-styled
discard modal. Changed-draft approval must submit through the live Streamlit
session, not the cold query-string snapshot reload. The component-rerun draft
bridge was rejected after two production failures because it exposed an
intermediate Object Detail render. The replacement stores the draft through the
authenticated `save_rfq_object_detail_draft` RPC and then triggers exactly one
native Approve callback; Objects quantity uses the authenticated
`save_rfq_object_quantity` RPC and updates the current DOM without a Streamlit
rerun. The additive migration was applied on 03.10.2026. Production acceptance
must compare both changed and unchanged Approve timing, confirm that quantity
save dims immediately, and confirm grouped money formatting and Materials totals
after editing any material row. The zeroed-Materials regression was traced to
ordinary rows rendering `data-policy-percent="—"`; the client calculator treated
every row as a pricing-policy row. Ordinary rows now render an empty attribute,
with a deterministic regression test. Changed-draft approval also writes the
recalculated totals and approved state together, removing the redundant second
authorization/read/write approval pass.

COMPLETED AND OWNER-ACCEPTED, P0, 3.15.25 Processing to File Review handoff
latency: the first File
Review render must reuse the exact validated Detection payload already persisted
by Processing instead of repeating ownership, run, detected-object, and usage
reads. Refresh and restored sessions continue loading Supabase. The complete
marker must not begin a deliberately extended gray interval. The zero-delay
candidate was rejected because the browser observer missed the marker and
exposed intermediate Streamlit DOM. Use only the bounded 120 ms handshake needed
by the existing 80 ms watcher, while preserving Cloudflare target readiness.
Production acceptance completed: the transition is fast, intermediate fragments
are no longer exposed, and the owner accepted the remaining gray interval of
approximately 1-2 seconds. Checkpoint: `5c322bf`.

HISTORICAL, SUPERSEDED FOR NEW PERFORMANCE WORK, 3.15.23 P0 authenticated full-reload optimization: production telemetry
shows that a hard reload frequently takes 6-8 seconds and can reach the
wrapper's 8-second fallback. Preserve the accepted Fast Resume and `app-ready`
readiness contract. The first candidate removes the legal release lookup from
authenticated Fast Resume and repeated session reruns, records product activity
off the render path, and performs the first Platform Admin and Last Estimate
lookups concurrently. Sign In still performs the required Terms gate. Do not
add a polling fragment or a second full-page rerun merely to activate header
controls. Treat the separate server-ready to browser-received delay as a
distinct Streamlit transport/render investigation, not as proof of slow Python.
The active transition pass also covers Upload, Profile, Admin, Partners, File
Review, Objects, and Object Detail navigation. Acceptance requires every normal
transition to complete within 3-4 seconds, no intermediate broken DOM, and the
destination opening at the top. Current production evidence isolates three
defects: Last Estimate repeats an already completed latest-estimate lookup,
Object Detail transitions lack target-ready closure and masking, and first-load
Partners/workflow routes retain transport or data-load outliers above 4 seconds.
The approved repair sequence is: close masked internal transitions from the
destination `app-ready` event, then keep ordinary Objects to Object Detail and
Back navigation inside the live Streamlit session. Object Detail approval keeps
its snapshot-bearing reload until editable-line persistence is redesigned, but
must preserve the wrapper trace so the destination can close the transition.
Production acceptance must also verify the authenticated navigation controls on
File Review. Server telemetry confirms that `account_controls_render` ran, but
the owner observed the control rail missing visually, so DOM visibility remains
unknown and is not closed by server-side render evidence.
Production checkpoint `7c81a5a` is owner-accepted for the current transition
speed, scroll-to-top behavior, and authenticated workflow navigation rail. The
owner confirmed that the rail now survives File Review, Objects, and Object
Detail navigation. This remains an intermediate performance checkpoint because
post-fix p50/p95 and remaining initial-load outliers are not yet closed.
The first native Object Detail bridge candidate did not intercept production
links reliably: Object Detail still opened under a new trace and caused three
15-second wrapper timeouts. The second and final bridge attempt must resolve
the hidden button by both key and label. Target-side scroll reset must run after
the destination DOM is ready because the earlier pre-render reset was later
overridden by Streamlit scroll restoration.
Source inspection identifies the workflow header alignment guard as the narrow
leading cause of the missing File Review rail: it selected the first workflow
title in the document and could align the fixed controls to stale Streamlit DOM
from the departing screen. The repair must select only a connected, visible,
non-stale title and clear the previous inline transform before aligning the
current screen.
Production acceptance confirmed that selecting a visible non-stale title and
scoping each workflow guard to its screen-specific title repaired File Review,
Objects, and Object Detail return navigation while preserving fast transitions
and scroll-to-top.
The 2026-10-03 Profile to Last Estimate outlier began a File Review server run
within about 0.50 seconds and completed auth plus membership in 237 ms, but the
run never completed `server.screen_render` or emitted `app-ready`. Earlier Last
Estimate evidence completed in 864 ms with a 22 ms screen render. Treat this as
a likely File Review/Supabase I/O outlier, not a transition-wrapper diagnosis.
If it repeats, add scoped timing around File Review data loading and then a
bounded timeout/recovery based on that evidence.
The later File Review regression is now isolated more narrowly: initial render
keeps the navigation rail, but the deferred Naming or Preview publisher issued
`st.rerun(scope="app")` when an artifact became terminal. That full rerun
unmounted the shared rail during Streamlit reconciliation. The active repair
keeps the rail and summary outside the two-second File Review fragment; only
object cards refresh from the persisted deferred artifacts. The earlier
File-Review-only stale-Upload CSS override is removed because it addressed the
wrong phase. Pending owner production acceptance: one run must retain the rail
while both a preview and an object name replace their placeholders.

COMPLETED, P0, 3.19.1 Contacts validation and normalization, owner accepted
10.10, commits `221d448`, `4709579`:
keep Street, House Number and City unchanged. Empty Contact fields remain
permitted. A non-empty Official email must match the existing shared email
syntax rule. Phone accepts an Israeli local number beginning with `0`, or an
international `+972` form, stores canonical E.164, and displays conventional
Israeli spacing. Website, Facebook, LinkedIn and Instagram silently remove an
entered `http://` or `https://`; Website must be a syntactically valid hostname,
while each social field must use its matching service hostname and a non-empty
profile path. A pasted `www.` is removed too, while placeholders retain their
example URLs. Postal code accepts exactly seven digits and strips non-digits at
input time. Email and every URL field strip non-ASCII characters at input time;
the server rejects any bypassed non-Latin value. There are no external network
lookups. Invalid fields receive only the existing Auth-red border and
the save is blocked, with no validation-copy block or extra Streamlit rerun per
edit. The implementation must retain values, clear a red state immediately
after correction, validate all submitted fields together, and reject a bypassed
client request on the server. Acceptance requires the authenticated production
matrix for empty fields, malformed and corrected values, pasted protocol URLs,
local and `+972` phone input, successful persistence/reload, and no regression
to Contacts Logo Save, the Profile rail, protected Price Lists or cold-load
behavior.

COMPLETED, P0, 3.20.1 Bank Details validation and normalization, owner accepted
10.10, commit `fcf0c78`:
Company registration number is exactly nine digits, retaining leading zeros.
Bank, branch and account numbers accept digits only, retaining leading zeros
without invented length limits. Bank and legal names remain free text. BIC is
uppercase Latin letters/digits in its standard eight- or eleven-character
format. IBAN removes spaces, converts letters to uppercase during typing and
paste, and must pass the international IBAN structure and MOD-97 checksum.
Invalid values use the existing Auth-red field border only and block Save,
without validation copy, external bank requests or per-edit Streamlit reruns.
Owner verified authenticated production coverage of paste, correction,
normalization, blocked invalid Save, saved reload and retained Profile behavior.

COMPLETED, P0, 3.18.1 authenticated Upload first paint, owner accepted 10.10:
instrumented the complete cold path and moved non-critical Platform Admin and
Last Estimate reads behind the first authenticated Upload reveal. The resulting
three owner production hard reloads were 3.05 s, 3.06 s and 3.23 s, median
3.06 s versus the immediately preceding comparable median 3.36 s. The server
critical-path median fell from 1.03 s to 0.28 s. Fast Resume remains one Python
run; RLS remains mandatory before authenticated content; no polling, second full
rerun, synthetic loading screen, or Price Lists behavior change was introduced.

COMPLETED, P0, 3.18.2 Profile first-paint and tab-latency measurement checkpoint,
owner accepted 10.10, depends on 3.18.1: live authenticated cold evidence records
the complete Upload-to-Profile and first-open tab path without changing the
owner-accepted Price Lists interaction contract. The production cold run measured
2.30 s Upload-to-Profile visible completion, with 2.27 s server work: 1.87 s
eager Profile import plus 0.37 s Overhead Expenses. First tab renders measured
Price Lists 0.49 s, Labor Costs 0.19 s, Company Details 0.19 s, Machinery 0.57 s,
and Users 0.64 s. The safe Price Lists projection-start hook did not produce a
confirmed pre-warmed Price Lists result in this owner trace, so this checkpoint
does not claim successful tab preloading. It preserves the 3.16.7 Price Lists
screen exactly: no callback, fragment polling, upload, Source, Review, DOM, toast,
or catalog-loading-contract change. Any renewed Profile performance work must use
this cold baseline and separately validate eager-import removal and tab warming.

COMPLETED, P0, 3.18.3 cold Sign in and authenticated bootstrap architecture,
depends on 3.18.1 measurements: optimise the worst customer path from Sign in
click through the first authenticated Upload reveal, and establish one measured
bootstrap architecture shared by cold Upload, Profile and Sign in. Record the
correlated browser, iframe, Streamlit-bootstrap, sign-in action, browser-session,
RLS, header-read, first-run and reveal timings. Do not count warm navigation as
acceptance. Prefer one coherent architecture over isolated wrapper micro-tweaks;
preserve Fast Resume, native authentication controls, one Python run where
possible, the accepted transition mask, and all protected 3.16.7 Price Lists
behavior. Owner acceptance on 10.10: Terms and membership gates now overlap only
after Supabase accepts the password, both remain mandatory before Upload, and
fresh Sign in to Upload traces reached 1.98 s, 2.46 s, 2.58 s and 2.98 s without
adding polling or a second Python run. Further wrapper/iframe bootstrap work is
deferred until a separately measured performance task.

PARTIALLY ACCEPTED, P0, 3.18.4 Profile Overhead and Pricing Cost editable-policy inputs:
make Monthly Cost and Total reciprocal whole-shekel inputs, with Arnona VAT exempt,
and add a visible Total monthly overhead expenses sum. The owner rejected the
last compact-Pricing spacing revision, but selected the preceding compact Pricing
surface: grouped Delivery / Installation, Consumables / Paint consumables,
Packaging, then policy fields with explanatory `?`. Numeric and percentage
inputs now follow the product-wide end-caret design-system contract. Preserve
canonical net-overhead persistence, owner-only
authorization, a single save boundary, and the accepted Price Lists, its fragments,
polling, upload, Source, Review and catalog loading behavior. Acceptance requires
authenticated production edits in both directions, Arnona invariance, correct total
sum, Pricing zero-clear/percent format behavior, aligned compact input columns,
hard-reload restoration of the selected Profile tab, save/reload persistence, and
no Price Lists regression. A cold restored session must render its complete
authorized header controls, including Admin when platform access exists. Owner
accepted the cold-reload speed checkpoint on 10.10: post-candidate visible
completion median was approximately 0.86 s versus approximately 1.08 s in the
preceding comparable sample. The Profile-tab durable-route defect is explicitly
deferred: Pricing Cost can still reload as Overhead Expenses. Do not add another
route experiment without a fresh authenticated reproduction and DOM/message-path
evidence.

ACTIVE, P0, 3.18.5 authenticated-session legal gate boundary, owner approved
10.10: Terms, Privacy, releases, documents and acceptance history are checked
only by the fresh successful password Sign in flow. Any already-authenticated
session resume, hard refresh, Fast Resume, browser-storage restoration, tab
selection, tool action or internal rerun must not read any legal source. A
failed fresh Sign in legal read remains a visible fail-safe error, never a
resume bypass. Membership and authentication checks remain mandatory. Verify in
authenticated production trace that resume contains `server.legal_terms_gate_resume_skip`
and no `server.legal_terms_gate_lookup`, then compare the cold timing with the
11:51 UTC baseline that spent 1.88 s in the legal lookup.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.6 shared authenticated header controls
in document flow, 10.10: Profile, File Review, Objects and Object Detail now
render the one existing authenticated action component beside their own title,
not as a root-level fixed rail. The controls leave the viewport together with
the screen title during document scrolling. Production implementation:
`b5bce72`; checkpoint: `notes/SHARED_HEADER_CONTROLS_CHECKPOINT_3_18_6_2026_10_10.md`.
The owner confirmed the previously persistent scrolling defect is resolved.
Preserved: action callbacks, authorized visibility, Upload placement,
transition readiness, scroll-to-top behavior, and the Price Lists contract.
No DOM mutation, client polling, uploader, callback or Price Lists behavior was
added. The rejected fixed, top-offset and absolute experiments remain reverted.
Visual refinement is not included in this accepted functional checkpoint and
requires a separately approved UI task.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.7 unified authenticated header geometry,
10.10: production implementation `b8bd3b0`, Object Detail completion
`9bd7339`; checkpoint:
`notes/UNIFIED_HEADER_GEOMETRY_CHECKPOINT_3_18_7_2026_10_10.md`. One shared
document-flow header component anchors the action rail to the title's local
header container rather than Streamlit-generated grid columns. The owner
accepted the resulting geometry across Company Profile, File Review, Objects,
Partners, Admin and Object Detail. Document-flow scrolling, callbacks, Upload
placement, transition readiness and the accepted Price Lists contract remain
protected.

COMPLETED AND OWNER-ACCEPTED, P0, 3.18.8 Object Detail hero-card vertical
spacing, 10.10: production implementation `8c0eb53`; checkpoint:
`notes/OBJECT_DETAIL_HERO_LAYOUT_CHECKPOINT_3_18_8_2026_10_10.md`. The Object
Detail second row now consumes the one native 16px Streamlit gap beneath the
accepted `Object:` header, without adding a duplicate top margin. Preview keeps
a matching 16px bottom clearance before the Cost/VAT/Total row. The owner
accepted the live authenticated result. Preserved: the accepted `Object:` /
navigation-controls axis, shared header component, callbacks, preview source,
totals, table calculations and responsive behavior.

DEFERRED, P2, USER REQUEST, 3.15.26 sleeping-session recovery feedback: when a
user refreshes Costerly after a long idle period and the application or session
must wake and restore authenticated state, replace the unexplained prolonged
gray screen with an explicit recovery state such as `Restoring your session`.
Show it only when wake or recovery is actually detected, not during ordinary
navigation or fast refresh. Preserve the accepted Fast Resume, authentication,
membership validation, transition masking, and no-intermediate-DOM contracts.
Acceptance requires a real long-idle production refresh, a truthful recovery
message while waiting, no broken screen fragments, and normal navigation once
restoration completes. Trigger: resume cold-start and session-recovery work.

COMPLETED AND OWNER-ACCEPTED, 3.15.23 Object Detail edit recovery: the
navigation rail remains protected by the accepted stale-state observer, and
material edits no longer collapse the full Materials section to zero. Browser
feedback is intentionally limited to the active row Cost. Enter or blur saves
the edit, and the server remains authoritative for policy rows, section totals,
VAT, and final self cost.
The first DOM-isolation candidate did not repair material recalculation: any
material edit still collapsed the whole Materials section to zero. The next
candidate removes formatted row-cost text as a calculation input and rebuilds
every material line deterministically from `unit_cost * quantity`, followed by
the locked policy percentages and section totals.
REJECTED: rebuilding client-side material totals from editable fields produced
the same zero-collapse. Stop the duplicate browser calculator. The accepted
recovery path saves the edited field on blur and lets the existing server
transaction recalculate lines, policy percentages, section totals, VAT, and
self cost before the refreshed Object Detail is shown.
RESOLVED: production evidence showed no line `updated_at` after an edit that had
not left the contenteditable field. Restore only current-row live Cost feedback
(`unit_cost * quantity`, or the equivalent Labor row formula), while blur or
Enter remains the single persistence and authoritative server-recalculation
boundary. Do not restore browser-wide section or final-total calculation.
DEFERRED, P2, 3.15.23 Approve transition optimization: production trace
`28dac1ea-5c35-40aa-9109-8246a22c2078` showed direct-link Approve creating a
new iframe/server session while the original transition reached its 15-second
timeout with zero Python runs. Reuse the accepted Streamlit bridge when the
Object Detail snapshot is clean. Retain the direct snapshot route only when
unsaved edits must be persisted atomically with approval. Code `89dda51` is
deployed and fully tested. Two clean production bridge cycles reached visible
Objects in 2.38 and 2.42 seconds and styled readiness in 3.41 and 3.44 seconds,
instead of the previous 15-second timeout. About 1.85 seconds consistently
passes before the destination Python run begins. When resumed, instrument
`_approve_current_object_and_return`, `approve_object_estimate`, deterministic
recalculation, and the approved-state write separately. If evidence confirms a
redundant full recalculation for a clean persisted snapshot, skip only that
duplicate work while retaining the atomic snapshot fallback. Trigger: owner
resumes transition-performance work.

PROPOSED, P1 background Terms reacceptance: authenticated Fast Resume does not
block initial rendering on the legal release lookup. Add a later background
version check and a blocking in-product modal that requires the current Terms
checkbox before the user continues. Preserve immutable acceptance evidence and
document that enforcement of a newly published version is delayed until that
background check runs.

COMPLETED AND OWNER-ACCEPTED, 3.15.22 Objects Estimation live result refresh:
replace the removed
React-DOM progress writer with a server-side Streamlit fragment that polls the
persisted per-object rows while the Estimation future is active. Preserve the
fast seeded first render, stop polling on terminal completion, and do not change
Cloudflare, authentication, workflow routing, or transition readiness. Local
candidate now also clears stale process-local progress, suppresses Streamlit's
stale-fragment dimming, and keeps Delivery, Installation, and Project Summary
visible with blank values until every object has a terminal priced result.
Production acceptance and the 861-test suite passed at `8b18fc3`. Full record:
`notes/OBJECTS_LIVE_ESTIMATION_CHECKPOINT_3_15_22_2026_10_03.md`.

Current owner-approved execution order:

ACTIVE, P0, 3.15.27 Anthropic token-cost accounting: record the cost of every
successful Anthropic model request from the usage fields returned by the model,
using the configured per-token pricing and preserving the existing request,
run, company, agent and model identity. The Platform Admin Detection,
Estimation and Price Source totals must include every such recorded request,
regardless of agent version or company. This is an application-calculated
usage cost, not a claim of an invoice-level provider debit. Mistral OCR is
explicitly excluded from this task and must remain unpriced rather than being
estimated from a public list price. Acceptance: nonzero Anthropic calls in all
three categories appear in the matching company row and in its total, while
zero, failed or unavailable events are visibly distinguished from a known zero.

DEFERRED, P1, USER REQUEST, 3.15.28 full provider billing reconciliation:
create a billing system that reconciles Costerly's request ledger with official
provider billing data, records reconciliation status and time window, and
never represents a local token calculation as an exact account debit. Design
the provider credentials, access controls, retention, aggregation boundary,
credit/adjustment treatment, and Mistral ingestion before implementation.
Trigger: after 3.15.27 is accepted and provider billing-data access is
available.

ACTIVE, 3.15.19 File Review editable project metadata: render Project name,
Partner, and Client as compact inputs using the accepted 52 px Overhead input
geometry. Persist edits only to the current RFQ run, keep drafts scoped by
run, and save the final visible values before Continue to Objects. Do not
create permanent Partner, Client, or Project catalog entities before Final
Approval. Local implementation and the 868-test suite pass. Remaining
acceptance: production deployment and owner verification of editing,
persistence, and unchanged File Review to Objects transitions.

COMPLETED AND OWNER-ACCEPTED, 3.15.18 Machinery session draft restoration:
restore the previously
accepted `722b6c6` interaction contract on the current performance baseline.
Machinery changes remain in the Streamlit session across Profile tabs and write
to Supabase only through one bottom Save action. Preserve the approved machinery
capability subset and existing domain model. Production acceptance must confirm
draft retention, one-save persistence, failure retention, member read-only
behavior, and the softer selected Yes/No colors. Production acceptance passed
at `1e1edaa`; full record:
`notes/MACHINERY_SAVE_AND_INITIAL_LOAD_CHECKPOINT_2026_10_03.md`.
The owner rejected the additional checkbox for changing a persisted in-house
capability to No: the explicit bottom Save action is the confirmation. Save must
not partially persist earlier rows and then stop on that removed UI barrier.

PROPOSED, P1 Machinery atomic batch persistence and Save visual polish: replace
the sequential multi-row persistence loop with one transactional RPC so a
transport or database error cannot leave a partial Save. Remove the single
fragment flash observed after an otherwise successful Save while preserving the
accepted session draft, success notice, and one-action contract.

ACTIVE, 3.15.17 Pricing Cost restoration on the accepted `d3e83bd`
performance baseline. The Pricing persistence and deterministic calculation
contract are restored without the later transition experiments. The Profile tab
is named Pricing Cost, follows Labor Costs, uses the Bank Details white
two-column form and one Save action, and keeps the compact eight-tab rail.
Local implementation verification passes. Remaining acceptance: deploy, verify
owner save and member read-only behavior, then repeat the protected production
transition timings before restoring Machinery or File Review metadata.

ACTIVE, 3.15.7 Labor reference-model foundation: checkpoint recorded in
`notes/LABOR_FOUNDATION_3_15_7_CHECKPOINT_2026_09_30.md`. Time baselines,
roles, drivers, source links, confidence markers, material-specific metal
routes, formulas, construction templates, crew rules, golden scenarios, and
the Labor Engine contract are prepared. Deterministic implementation is active:
five templates are implemented and 40 targeted tests pass. Next: complete the
remaining approved templates, batch aggregation and all ten golden scenarios.
The Estimation Agent replacement remains a later task. Full continuation is in
`notes/MATERIALS_LABOR_NEXT_CHAT_HANDOFF_2026_09_30.md`. This priority does not
cancel 3.15.4 through 3.15.6; they remain pending at their recorded checkpoints.

ACTIVE, pending Railway deploy, auth regression: pressing Enter while focused
in the Sign in password field must submit Sign in, never trigger Forgot
password. The local 29.09 observation proved that Streamlit selects the first
form submit button, which was Forgot password. The local implementation is
complete. Preserve recovery and verify it in the real authenticated production
browser after Railway becomes available.

UI follow-up, local Price Source: inspect and correct the observed green-on-green
status treatment. Reuse the accepted production status-token hierarchy, then
validate the actual rendered local and production states. Do not infer the
cause from the local screenshot alone.

0. Backlog, cross-agent failure observability: record every attempted run before
   network, file, model, or persistence work begins. Keep an internal failure
   record with agent name, company-safe correlation ID, input type and URL/file
   metadata, stage, bounded diagnostics, timing, model/provider metadata, and
   sanitized error. Build an internal review queue with retry, evidence view,
   grouping by failure signature, and alerting for repeated or systemic failures.
   Scope: Detection, Estimation, Price Source, Material Identity, and future
   agents. This is internal only, must not expose one company's content to
   another, and must not slow the happy path. The current Tsidky URL fetch
   failure is the first acceptance case.

1. Finish 3.15.4 Price Source integration with the shared Material Resolution
   Core. Detailed checkpoint: `notes/PRICE_SOURCE_MATERIAL_RESOLUTION_3_15_4.md`.
2. Run the first representative production Price Source through the resolver
   and accept exact, shortlist, and unmatched behavior with real evidence. The
   second Tsidky run is not accepted: service separation improved, but canonical
   resolution and the bounded Identity Agent failed their acceptance criteria.
3. Build the internal material identity review interface as task 3.15.5. Staff
   must be able to inspect the source evidence and bounded shortlist, link an
   existing reference material or create a reviewed new identity, preserve an
   immutable decision audit, and publish a confirmed alias for future imports.
   This is an internal Admin workflow, not a required company-user action.
4. Optimize Price Source end-to-end latency as task 3.15.6. Benchmark URLs,
   PDFs, spreadsheets, and photos separately; measure fetch or upload, parsing,
   model time, legacy material and offer persistence, identity resolution, and
   final UI refresh. Batch remaining row and offer writes, avoid repeated reads,
   preserve accuracy and audit behavior, and add honest stage progress or a
   recoverable background workflow for genuinely long runs. The first URL
   baseline was more than two minutes: 60.6 seconds in the model, about 31
   seconds in legacy persistence, and about 36 seconds in the original
   sequential identity stage. The identity stage is already batched; its new
   production timing remains to be measured.
   Coatings pricing coverage is a separate deferred input task: seek an
   evidence-backed Israel B2B catalog or invoice from a professional factory
   coatings channel, beginning with Sayerlack through its Israeli professional
   representative. Do not seed Israel baseline prices from retail suppliers or
   foreign retail prices. Preserve real purchase-pack prices. A price-per-liter
   figure may only be a comparison fact inside a comparable product line, never
   the estimation fallback price.
5. Complete operations, labor, machinery, and subcontractor reference models.
6. Replace the legacy Estimation Agent only after those inputs are verified.

- 3.15.4 Price Source Material Resolution integration: active, P0. The
  implementation candidate routes every activated Price Source row through the
  shared resolver after extraction, so historical rows can be processed without
  repeating OCR. Exact identity links the private company material to the
  reference catalog. Shortlists and unmatched identities remain private and
  enter the review buffer. Resolution events are append-only, same-version
  batch reruns are idempotent, and resolver failure does not invalidate a
  completed price import. Production currently has zero Price Source rows, so
  the historical pass correctly examined zero rows. The first production URL
  then extracted 47 rows: 41 price-ready, one unresolved, and five excluded;
  identity resolution produced two exact links and 39 bounded shortlists. That
  run exposed a latency regression: sequential identity writes added about 36
  seconds after the 60.6-second agent call and about 31 seconds of legacy row
  persistence. The resolver candidate now batches candidate, source-row, and
  audit writes. A 40-row regression test enforces one write per destination
  table. Full suite: 657 passed. Production timing acceptance remains pending.

  P0 production acceptance blocker from the second Tsidky run on 29.09: v5
  extracted 51 rows, with 37 active prices, five evidence-based unresolved rows,
  and nine operation-service rows correctly excluded. This fixes the earlier
  error where four edge-banding application rows became materials. Preserve and
  regression-test this rule for cutting, drilling, machining, edge-banding
  application, assembly, installation, and delivery on similar supplier pages.
  Canonical resolution is not accepted: zero rows linked, 36 returned
  `no_compatible_identity`, and one returned a shortlist. The resolver currently
  treats a canonical material's missing stored specification as a conflict with
  every extracted attribute, so useful candidates disappear before the agent.
  Change retrieval so only explicit contradictory hard attributes reject a
  candidate; missing canonical attributes reduce confidence and remain visible
  to bounded comparison. Add controlled family-to-category retrieval for sheet
  materials and solid timber without widening automatic-link rules. Correct
  Israeli timber section notation such as `5/2.5` to an evidence-based 50 x 25
  mm section instead of `5 x 2.5 mm` or diameter. The bounded Identity Agent
  produced no recorded decisions in this run; stop swallowing that failure,
  record its error and timing, call it only for rows with useful bounded
  candidates, and preserve the 90 confidence plus no-hard-conflict auto-link
  gate. Reprocess the persisted source rows through the corrected resolver
  without repeating URL extraction, then accept service exclusion, candidate
  recall, automatic links, review routes, latency, and immutable audit together.

- 3.15.3 Material Resolution Core: completed, P0. The deterministic candidate
  resolves exact supplier SKU, company alias, market alias, hard attributes,
  then a maximum-five shortlist. The production read-only benchmark returned
  797/797 correct unique alias matches and 201/201 correct unique supplier-SKU
  matches, with zero false resolutions across five collision keys. The additive
  schema migration is applied to production. The active resolver is
  `material_identity_v1`; all four protected tables were verified through the
  service role before 3.15.4 began.

- 3.15.2 Israel material baselines and furniture-core completion: active, P0 by
  owner direction. The production activation checkpoint is verified: 280
  active v1 baselines cover 280 distinct materials, retain 331 evidence links,
  have complete approval metadata, and expose confidence 10 to 65. The next
  checkpoint is also complete: the isolated company-first resolver handles
  VAT-exclusive normalization, compatible units, multiple supplier ranges,
  price-scope separation, baseline fallback, and explicit review results. A
  production batch resolves all 280 active catalog materials, but production
  has no company material offers yet. Next, Price Source must link recognized
  company items to `reference_material_id`. Automatic Estimation fallback,
  widened identity linking, and private-data market learning remain separate
  decision gates.

- 3.15.1 Israel Reference Catalog foundation: completed at `1f8d6ab`.
  The ordered master plan is `notes/ISRAEL_REFERENCE_PROGRAM_PLAN.md`. Its
  Packages A through J preserve the accumulated material and price work and add
  the approved shared Price Source, identity-candidate, market-learning,
  operations, review-governance, and Estimation-readiness sequence. Production
  now contains the verified schema, identities, profiles, candidate offers, and
  aliases recorded in `notes/ISRAEL_REFERENCE_CATALOG.md`; continuation moved
  to 3.15.2.
  Replace the empty legacy material, work-time, and machining-points foundation
  with a multi-market reference architecture. Global material, operation, and
  labor-role identities remain separate from market-specific prices, local
  specifications, and productivity standards. Israel is the first explicit
  market (`IL`, `ILS`), and cross-market fallback is forbidden. Company data
  remains first priority; an exact Israel baseline is second; unsupported scope
  returns `needs_review`. The schema candidate deliberately contains no invented
  price or time seeds. The candidate taxonomy now contains 82 material
  categories, 43 physical drivers, 77 operation identities, and 29 labor roles.
  The first seven sourced Israel batches add 76 exact material identities and
  85 observed offers: 24 panel offers, 16 fixed-price Blum hardware offers, one
  galvanized steel stock-length offer, five coating/consumable offers, and 14
  solid-wood/OSB offers, nine PVC edge-band offers, plus sixteen acrylic offers
  covering eight raw sheets and eight cut-to-size equivalents.
  `notes/ISRAEL_REFERENCE_MASTER_CHECKLIST.md` is now the fixed coverage
  denominator: 395 materially distinct estimation cells across wood, metal,
  glass, stone, plastics, hardware, fasteners, coatings, consumables,
  upholstery, electrical components, installation, and packaging. Current
  evidence closes 2 cells and partially covers 21; 372 remain empty.
  None is promoted to an active market baseline from a single or incomparable
  source. Continue source coverage and independent-source comparison before
  activation. Before additional broad source harvesting, integrate the accepted
  shared Material Resolution Core contract with Price Source. Ordered backlog:
  (1) define the shared reference, company, source-offer, and identity-candidate
  cards; (2) unify category, specification, unit, alias, scope, provenance, and
  confidence vocabularies; (3) add the candidate lifecycle and immutable review
  audit; (4) route Price Source through exact SKU, company alias, Israel alias,
  hard filters, and a maximum-five shortlist; (5) link matched company items to
  `reference_material_id` while keeping unmatched usable items private; (6) add
  a separate eligibility gate for anonymized market observations; (7) make
  reviewed identities and aliases available to future imports through a
  versioned resolver index; (8) specify merge, split, deprecation, remapping,
  and historical reprocessing behavior; (9) build the staff review tool after
  the lifecycle and permissions are verified; (10) apply the complete migration
  chain to a clean database and test idempotency, tenant isolation, rejection
  cases, and reprocessing before activation. The review tool is explicitly in
  backlog and is not part of the current schema-contract revision. Contract:
  `notes/ISRAEL_REFERENCE_CATALOG.md`.

- 3.14.1 CNC / Laser costing foundation: active, P0 by owner direction. The
  owner promoted this task to the highest current priority on 28.09. Follow
  `notes/CNC_LASER_FINISH_PLAN_2026_09_28.md`. C1 production schema is verified;
  C2 read-only Staff Admin has a tested implementation candidate awaiting live
  acceptance. The material catalog remains preserved but paused until the CNC
  subsystem reaches its production checkpoint. The calculation engine is
  demand-driven and runs only a required process for one
  homogeneous part group. CNC `Yes` means in-house. CNC `No` uses a narrow
  panel-saw plus manual route only for simple low-volume rectangular work and
  otherwise uses a CNC subcontractor. Sheet laser `No` defaults strictly to a
  subcontractor; rough basic in-house cutting is a rare explicitly confirmed
  exception. The active CNC route has one explicit estimate level
  from 1 to 5; level 3 is the effective untouched default and is not feedback.
  Explicit changes append a bounded behavioral-calibration event without
  estimate cost or customer content. The local candidate passes 514 tests.
  `db/sql/2026_09_28_cnc_estimate_levels.sql` and the broader manufacturing
  parameter migration were applied to production on 28.09. The isolated
  deterministic router, exclusive calculator dispatch, four pure calculators,
  reserve-level selection, supplier-minimum handling, inclusion boundaries,
  parameter snapshot IDs, and scenario fixtures are implemented and pass the
  full suite locally. Active parameter resolution now enforces exact scope,
  containing thickness bands, provider isolation, units, currency, effective
  dates, approval, provenance, and explicit missing or ambiguous review states.
  It never selects the nearest unsupported scope. None of this is connected to
  current Estimation results. Continue with Revision A migration review and the
  read-only Admin parameter library.

- 3.12.1 Price Source Agent accuracy: historical tracking, superseded by active
  3.16.7 for current implementation and acceptance. Preserve the following
  revision history as evidence, but record all new Source Agent work only under
  `notes/PRICE_LISTS_REBUILD_3_16_7.md`. Improve real supplier-source
  extraction, material-type classification, unit normalization, confidence,
  and ready-versus-unresolved decisions while protecting the accepted 3.10.1
  Price Catalog UI checkpoint `d18b533`. The approved v3 candidate adds row-level
  Material Type, document number and totals, VAT evidence, semantic duplicate
  protection, and Source Details timing and TC. Automated verification and a
  representative production evidence pass remain required. Revision 2 now
  separates extracted and active counts in the completion notice, shows time
  and TC immediately, removes manual Price Source reruns, and restores native
  file-delete hit testing. Revision 3 removes confidence as an activation gate,
  blocks only price-critical VAT and package-conversion uncertainty, standardizes
  normalized names, and adds row-level Review, Edit, and Remove. Revision 4 moves
  those actions into the main catalog, exposes unresolved rows in a visible Needs
  review block, removes whole-source deletion, and repairs the client-only stuck
  Extracting prices state. Revision 5 treats repeat uploads as row-level update
  checks: exact duplicates skip the agent, changed inputs report new, updated,
  unchanged, and unresolved counts, unchanged offers are not rewritten, and
  missing rows are preserved. It also restores the accepted compact catalog
  geometry after the row-action visual regression. Revision 6 opens only the
  original source from Source/View, paginates Needs review for responsive row
  actions, marks only activation-blocking fields, removes duplicate editor
  headings and row gaps, and suppresses non-informational hover tooltips.
  Revision 7 preserves that geometry, lowers the Needs review labels by 3 px,
  removes duplicate fragment reruns, and reuses a tenant-scoped read snapshot
  for fast UI-only actions while invalidating it after every data mutation.
  The owner accepted revision 7 in production at `d99a594` as the fast working
  Price Lists interaction checkpoint. Visual polish is not final, but further
  agent-accuracy work must preserve this version. Revision 8 adds internal
  source-family and revision metadata for recurring files and URLs while
  retaining exact-duplicate short-circuiting and row-level new, updated,
  unchanged, and missing behavior. Revision 9 prevents invalid multi-document
  selections from entering processing. Revision 10 block A adds first-class
  internal-estimate and customer-sale provenance, keeps internal rows reviewable
  until their isolated offer lane exists, and deterministically excludes selling
  prices from material costs. Revision 11 adds an explicit server completion
  marker so a completed run cannot leave the optimistic Extracting prices state
  behind. Revision 12 makes that marker processing-cycle aware, so an old idle
  marker cannot immediately cancel the next click's progress state, and removes
  the misleading zero unchanged count from unresolved-only duplicate results.
  Revision 13 establishes the MVP uploader contract: multiple JPEG/PNG pages
  remain one logical document, while PDF, XLSX, and CSV keep only the first
  selected document. In a mixed selection, the first file selects the route:
  photo-first keeps all JPEG/PNG pages, document-first keeps only that first
  document, and a compact note explains the rule when files are rejected.
  Photos retain a four-column, two-row scrollable grid; a single document gets
  a centered enlarged card with a readable name. Revision 14 block B1 adds a
  first-page PDF preview and structural XLSX/CSV template identity so renamed or
  value-updated workbooks remain auditable revisions of one source family.
  Revision 15 extends real previews to XLSX, CSV, JPEG, and PNG, blocks a second
  PDF/spreadsheet against the document already rendered in the uploader rather
  than only filtering the latest picker batch, and keeps every completed
  Extract result visible until the next Extract attempt. Sequential JPEG/PNG
  pages remain supported as one photo document. Revision 16 isolates the
  invalid-second-document drag state: the accepted chip and preview stay
  visible, only the existing card border turns red, leaving the zone clears the
  red state immediately, and the yellow explanation appears only after reject.
  The owner accepted the complete uploader behavior in production at
  `1a2d7ca`; this is the rollback checkpoint for upload selection, previews,
  repeat-result feedback, and occupied-zone drag indication.
  Revision 17 block B2 is now a tested production candidate. Internal estimates
  activate only when VAT and package conversion are resolved, stay in the shared
  Material Prices catalog without a fake supplier, and version within their
  recurring source-family lane. Supplier, unknown-supplier, unrelated internal,
  and reviewed-row offers remain isolated. The full suite passes with 403 tests.
  Production acceptance remains pending for one internal workbook, its changed
  revision, and coexistence with a supplier offer for the same material. After
  that evidence, source-level VAT confirmation is block C. Mixed-document
  queueing remains deferred under 3.12.3, and resolver priority remains deferred
  until both offer lanes have production evidence.
  Revision 18 block C1 is now a tested candidate. Needs Review can apply one
  explicit currency and VAT basis to a persisted internal source without another
  agent call. Complete positive unit prices can enter the B2 internal lane even
  when line quantity is zero; unresolved units or conversions stay in review;
  deterministic non-material cost rows are excluded. The full suite passes with
  407 tests. Production acceptance on the latest internal workbook remains
  required before C1 becomes a checkpoint.
  Contract: `notes/PRICE_SOURCE_AGENT.md`.

- 3.12.2 Cross-agent Token Cost observability: pending, P1 after the Price
  Source Agent cost display establishes the shared convention. Show compact
  `TC X.XXX` per completed run and total cycle from persisted provider usage
  without double counting. Preserve model, prompt version, input/output tokens,
  configured pricing source, and unavailable-cost state. Apply to Detection,
  billable OCR, Naming, Estimation, and future agents.

- 3.12.3 Batch Price Source ingestion: deferred after MVP, P2. Let an owner drop several
  independent PDF, spreadsheet, and image documents in one action, split them
  into logical sources, and process them through a bounded sequential queue.
  Each source needs its own validation, progress, result, retry, duplicate or
  revision decision, timing, and TC so one bad document cannot block or obscure
  the others. Preserve the existing rule that several JPEG/PNG pages may form
  one logical document; grouping mixed photos into documents needs an explicit
  user or deterministic grouping contract before implementation.

- 3.12.4 Existing email registration guard: tested candidate, P1. After an
  invitation signup is submitted, treat Supabase's obfuscated existing-user
  response and explicit `email_exists` response identically. Keep the signup
  form open, mark Email, and show `This email already has a login. Sign in or
  use another email`. Do not create a pending legal registration, legal event,
  company, or membership, and do not consume the invitation. The full suite
  passes with 409 tests. Production acceptance with one existing address and
  one fresh address on the same unconsumed invitation remains required.

- 3.9.1 Machinery and production routing foundation: active, P1. Add a compact
  16-capability profile across woodworking, metalworking, and finishing while
  retaining the 27-row database catalog for compatibility and history,
  with wood CNC and metal laser cutting as separate first-class capabilities.
  Company owners record explicit in-house availability, minimum technical
  limits, costing basis, and optional regular subcontractors only for operations
  that are realistically outsourced. Saved rows collapse to a summary and
  multi-value capabilities use selectable pills. The additive Supabase migration was applied on 24.09:
  all five new tables are available, the catalog contains 26 active rows, new
  company tables are empty, anonymous catalog access is denied, and all 124
  prototype `company_machines` rows remain untouched. The owner/member Profile
  UI, deterministic production-context snapshot, and automated scenario
  coverage are implemented locally and 291 tests pass. The real owner/member
  production pass, mobile/keyboard pass, commit, deployment, and acceptance remain pending. The production
  context is not sent to Anthropic until the owner explicitly approves transfer
  of private machinery, supplier, and pricing data or approves a sanitized
  payload contract. Continue from `notes/MACHINERY_FOUNDATION.md`.

- 3.8.1 Railway hosting migration: accepted production checkpoint. Preserve
  production checkpoint `bbb8297` and retain the Streamlit Cloud deployment as
  rollback while the existing Cloudflare wrapper runs against Railway at
  `app.costerly.ai`. The
  wrapper selects the Railway backend only for the staging hostname and uses
  the selected backend origin for all transition handshakes. Acceptance
  requires clean hard refresh, Sign in, Upload to Profile, Profile to New
  Estimate, Profile to Upload, and Sign out cycles without gray, white,
  unstyled, or mixed-screen frames, plus complete correlated runtime telemetry.
  Direct Railway testing is not visual acceptance because it bypasses the
  Cloudflare transition wrapper. The owner explicitly approved switching the
  production wrapper backend to Railway after confirming the direct Railway
  runtime was materially faster. The owner completed repeated Sign in, Profile,
  New Estimate, return, and Sign out cycles and accepted the result as fast and
  production-ready. Trace `a6152e2d-517a-4faa-a125-311c46faa3ef` measured the
  initial Auth reveal at 4.011 seconds; accepted warm styled reveals were mostly
  0.677-1.356 seconds with one Python run. Known acceptance gap: one first
  Profile cycle after a repeated Sign in hit the five-second mask timeout and
  reached ready at 10.869 seconds, and the owner observed one negligible broken
  frame. Retain both as follow-up evidence rather than claiming zero visual
  defects. Verification: 238 tests passed. Checkpoint commit: `4b8b24a`.
  Protected production checkpoint: `bbb8297`.

- 3.8.2 Password recovery: closed by owner on 24.09 without further production
  acceptance work. The working flow and email changes remain preserved at
  checkpoint `f1de50e`; do not treat the former Gmail and full-matrix follow-up
  as active unless the owner explicitly reopens it. The historical contract and
  unresolved verification record remain in `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md`.
  The completed implementation added a user-visible
  Forgot password flow using the existing Supabase Auth account and the final
  branded application origin. Reuse the accepted Sign in visual and transition
  system, keep account-existence responses neutral, use a single-use expiring
  recovery link, and enforce the registration password policy on reset. Verify
  the actual Supabase recovery-mail transport and redirect contract before
  implementing the production send path. The recovery email and browser-session
  handoff now reach the Reset password form. Production password submission
  was verified by the owner on 23.09: the form changed the password, returned
  to Sign in, and the new password authenticated successfully. The remaining
  active scope is production visual acceptance of the Sign in feedback layout:
  Password and Forgot password share one label row, feedback appears only when
  needed below the input, moves the primary button by one compact line, and
  disappears immediately when the user resumes editing. Production recovery
  acceptance must cover partial Sign in input, syntactically invalid email,
  wrong credentials, recovery immediately after a failed Sign in, and reset
  validation in strict order: password policy first, password match second.
  Server-rendered field markers must replace stale client validation state, and
  every new feedback response must become visible even when Streamlit reuses
  the previous DOM container. Production verification of this sequence remains
  pending. The production recovery mail must also use the repository subject
  template
  `Reset your Costerly AI password [{{ .TokenHash }}]` so every
  request has a distinct subject and mail clients do not thread separate
  recovery attempts together. The HTML template must remain in its light
  Costerly AI palette in dark-mode mail clients, using email-compatible color
  declarations rather than relying on client theme defaults. The hosted
  Supabase template is external state and both changes must be verified
  independently after applying the repository values. The 24.09 Gmail iOS
  screenshot verified that the light background and logo survive dark mode,
  but Gmail still inverted the main paragraph to white. The repository
  template now applies the Gmail blend-mode text guard and removes the nested
  gray page, bordered card, and rounded card treatment in favor of one flat
  white message surface. Production verification remains pending after the
  updated HTML is copied into Supabase and a new recovery message is generated.
  Continue from `notes/AUTH_PASSWORD_RECOVERY_HANDOFF.md`. The owner established
  a mandatory scenario-first UI rule on 24.09: every interface revision begins
  with a complete agreed behavior matrix, and implementation, automated tests,
  and production acceptance must follow that same matrix. Do not resume 3.8.2
  through isolated visual patches.

- 3.8.4 One-time team invitations and access removal: completed and accepted in
  production. The owner confirmed the additive Supabase migration was applied
  on 22.09. Each freshly generated bearer link is not tied to an email, expires
  after 24 hours, and is consumed atomically by the first successful membership
  creation. The Users tab lets only the owner generate a link and remove a
  member after confirmation; the owner cannot remove themself. Removal deletes
  only the `company_members` relationship, not the Supabase Auth user. The
  legacy `company_join_links` table remains untouched as a rollback surface but
  is no longer read by the new application path. Verification covered one
  successful registration, rejection of the consumed link, member removal,
  fresh access denial for that member, and preservation of Profile -> Users
  after link generation. The owner-facing raw token is plain text with a
  dedicated Copy action, never a navigable link. The Join registration screen
  reuses the accepted Sign in heading, full-width submit geometry, validation,
  loading spinner, and retained-screen transition behavior, without the
  redundant explanatory subtitle. The owner accepted the production result on
  22.09. Implementation commits: `013a67b` and `15d5aea`. Railway required a
  manual Deploy Latest Commit because the expected GitHub autodeploy did not
  trigger; that deployment-integration defect remains a separate follow-up and
  does not invalidate the accepted invitation behavior. Verification: 244 tests
  passed.

- 3.8.5 Railway GitHub autodeploy reliability and build timing: completed, P1.
  GitHub `main`
  accepted commits `b9f27d4` and `785d828`, and Cloudflare Pages deployed the
  same source automatically, but Railway did not create a deployment until
  `Deploy latest commit` was triggered manually. Verify the service Source is
  connected to `kzhivin-lgtm/costerly-app` on `main`, Autodeploy is enabled,
  Wait for CI is disabled while no GitHub Actions workflow exists, Watch Paths
  are empty, and Deployments has no skipped or approval-waiting pushes. Then
  prove the repair with one harmless GitHub commit that produces a Railway
  deployment without manual intervention. The baseline deployment exposed
  approximately 112 seconds of build work, including 51 seconds for pip, while
  Railway displayed more than four minutes end to end. The current experiment
  replaces `requirements.txt` with the standard `pyproject.toml` plus `uv.lock`
  path recognized by Railpack 0.39.0 and Streamlit Community Cloud. Local cold
  dependency preparation completed in 7.49 seconds and installation in 0.197
  seconds. Commit `bf0581d` proved the repair: Railway created deployment
  `4dec029a-5989-419c-8be8-751f1e41c954` automatically 16 seconds after the
  push timing mark, selected uv on Railpack 0.39.0, passed its healthcheck, and
  reported success after 193 seconds. Explicit build steps fell from about 113
  seconds to about 72 seconds, a reduction of roughly 41 seconds or 36 percent.
  Approximately 114 seconds before server start remain outside the itemized
  build steps and belong to Railway scheduling and deployment orchestration,
  not dependency installation. Verification: 263 tests passed and both the
  direct Railway health endpoint and `app.costerly.ai` returned HTTP 200.

- 3.6.2 Hard-refresh Sign in reveal stability: preserve the accepted in-button
  spinner and one-run Sign in while preventing partial Upload DOM from appearing
  after Command-Shift-R. Production trace
  `eaf99421-c863-4886-ac74-e34f8d56298b` measured Sign in at 1.106 seconds with
  one Python run, target visibility at 1.077 seconds, and app-ready only 29ms
  later. Replace the insufficient two-frame release criterion with 120ms of DOM
  quiet and a 450ms fail-open. Status: accepted production checkpoint at
  `fb1ad97` (v3.6.2). The user confirmed fast Sign in, the accepted in-button
  spinner, and no partial screen in the tested hard-refresh cycle. Protected
  rollback points: v3.5.11 (`aa05a5d`) and v3.6.1 (`f334338`).

- 3.6.1 Labor Costs table compaction: fit the complete worker summary table
  inside the Profile content width without horizontal clipping. Stack Edit and
  Remove vertically in a narrow action column, show `Hourly` and `Monthly` only
  in the table, omit the employment factor from Pay Details, and size the
  controlled-value columns around their longest supported labels. Shorten the
  managed Position labels, remove Cabinetmaker / Joiner and Purchasing Manager
  from new selections, and hide the optional clear control in the three Labor
  Costs selectors without changing their dropdown action. Existing archived or
  active records retain their stored codes; the retired cabinetmaker code is
  presented as Carpenter. Status: accepted in production at `f334338`
  (v3.6.1); the user confirmed the compact table result. Protected rollback
  checkpoint: v3.5.11 (`aa05a5d`).

- 3.5.2 Profile and Auth performance stabilization: keep v3.4.2 (`86117ba`)
  as the emergency rollback boundary without treating it as a measured speed
  baseline. Split the first Profile path into lazy module import, Profile shell,
  styles, header, tabs, and active content. Use complete production traces to
  identify the earliest slow boundary before changing behavior. Restore warm
  Profile and Auth transitions to the previously accepted range, retain native
  Streamlit actions, encrypted Fast Resume, sessionStorage fallback, route
  restoration, and the Cloudflare transition mask, and accept only after two
  complete user-visible cycles show no broken intermediate screen.
  Production evidence for candidate 3.5.6 identified and removed a redundant
  Upload-to-Profile rerun: navigation now changes screen state in the native
  Profile button callback before the next script render. Acceptance remains
  pending a deployed full-page reload with matching wrapper/server build and
  two clean cycles. The next isolated target is the 1.9-second synchronous
  browser-session store measured during Sign in.
  Regression protection now includes a shared callback-safe screen setter, a
  source test rejecting widget navigation followed by explicit rerun, a
  wrapper/server build handshake with one guarded reload, and per-transition
  Python-run counts. Production acceptance must show matching builds and
  `python_runs=1` for both Profile directions. Status: accepted production
  checkpoint at `aa05a5d` (v3.5.11). The user confirmed satisfactory behavior,
  the in-button Sign in spinner, and clean transitions. The first cold Upload
  to Profile remains somewhat slower than repeated transitions and is accepted
  for this stage rather than retained as an active defect.

- 3.1.12 Refresh route persistence: after browser refresh, restore the same
  authenticated product screen and, where applicable, the same nested tab.
  Apply one explicit navigation-state contract to Profile, File Review,
  Objects, Object Detail, Registration, Company Setup, Auth, and future screens.
  Preserve authorization checks and never restore a company-scoped resource
  without revalidating access. The current revision mirrors only safe route
  state into the outer Cloudflare URL, forwards it to each new Streamlit iframe,
  restores the selected Profile tab and persisted RFQ/estimate/object context,
  and reuses the existing Supabase ownership checks before rendering protected
  resources. Auth and invite-driven screens remain derived from their existing
  authorities. Active Processing intentionally fails safe to Upload because its
  file bytes and futures are not durable yet. The first production revision
  restored Profile after shared account controls had already rendered, causing
  duplicate `company_sign_out` keys. The corrected revision restores Profile
  and its tab before account controls render. The Cloudflare transition layer
  now covers both Profile to Upload and Upload to Profile while the restored
  screen is assembled. Status: accepted production checkpoint at `e48bb71`;
  the user confirmed refresh preserves Profile and its selected tab, no
  duplicate-key error remains, and both transition directions are clean.

- 3.1.11 Profile to Upload transition integrity: identify and remove the
  intermediate stale or partial screen visible after Continue to upload.
  Preserve the accepted Profile and Upload layouts, native button behavior,
  transition telemetry, and the v3.1.10 navigation callback. Production logs
  confirm a 0.712-second click-to-ready transition with only 0.291 seconds of
  server work and a 1.3ms Upload render; the visible defect is Streamlit's
  incremental client DOM patch while the old Profile marker is still present.
  The current revision reuses the Cloudflare startup mask only for this
  transition, reveals the iframe on the correlated Upload `app-ready`, and has
  a five-second fail-open timeout. Status: accepted production checkpoint at
  `4738cb3`; the user confirmed no intermediate screen in either direction
  between Profile and Upload.

- 3.1.10 Company Profile navigation and Overhead Expenses copy: restore the
  accepted v3.0.57 full-width tab rail on the current stateful, lazy-rendered
  tabs without reverting the v3.1.8 performance improvement. Use Overhead
  Expenses consistently in the table heading, save action, success message,
  and save errors. Remove the current React Aria selection underline, emphasize
  only the active tab, and remove the zero-height save bridge from document
  flow, including its outer Streamlit element wrapper, so Overhead Expenses
  starts at the same height as Contacts. Rename Price List to Price Lists.
  Preserve the working expense persistence path and defer Sign out sizing,
  Save Contacts, and Save Company Details. Status: production work-in-progress
  at `9ab5814`. The rail, active-tab bold treatment, plural `Price Lists`,
  Overhead Expenses copy, working Save, and removal of the red React Aria
  indicator are visually confirmed. A small residual vertical offset remains
  between the Overhead Expenses card and the other tab contents. Do not add a
  guessed negative margin. The accepted rollback boundary is `b58b1f5`, restored
  without history rewriting at `6a403b0`. Production telemetry then confirmed
  that the remaining whole-page jump is not scrolling or tab CSS: the transient
  zero-height `scroll_parent_to_top()` component occupies one 16px root layout
  gap on the first Profile render and disappears on the tab rerun. The current
  revision moves that utility component into the hidden Sidebar while preserving
  its scroll-reset behavior. The remaining Expenses-only offset was addressed by
  limiting `@st.fragment` to the save bridge instead of wrapping the complete
  tab. Profile to Upload navigation now changes screen state in a pre-render
  callback, preventing a partial Profile delta before the Upload rerun. Status:
  accepted production checkpoint at `3f8c80a`; the user confirmed the page no
  longer jumps, the Expenses alignment is correct, and Save remains functional.

- 3.1.9 Auth transition integrity: execute Sign in and every Sign out through
  native Streamlit callbacks before the next script render. Remove the
  intermediate Login/Profile render that can expose a broken screen or two
  logos. Preserve the current cookie, sessionStorage fallback, telemetry,
  native click behavior, and accepted layout. Status: functional production
  acceptance at `8182c51`. Clean Sign out measured 0.75-1.22 seconds and clean
  Sign in measured 1.29 seconds, with no broken screen observed. A telemetry
  follow-up closes failed Sign in transitions so later successful timings do
  not inherit stale correlation IDs.

- 3.1.8 Profile latency optimization: preserve the accepted six-tab geometry
  and working Save Expenses path, but render only the selected tab. Reuse the
  company access already verified in the current Python run and load the
  company profile row only for Contacts or Company Details. Status: accepted
  production checkpoint at `4c6d628`. Repeated Upload to Profile improved from
  3.36 seconds to 1.06-1.12 seconds, with server time reduced from 2.36 seconds
  to 0.29-0.30 seconds. The first cold transition improved from 4.23 seconds
  to 2.66 seconds.

- 3.1.7 Internal transition telemetry: measure Sign in, Upload to Profile,
  Profile to Upload, and Sign out from the browser click to the next rendered
  screen. Correlate each result with auth network time, company access lookup,
  Profile load, screen render, and Python reruns. The browser observer is
  passive and bubble-phase only. It must never cancel, delay, disable, or
  replace a native Streamlit click. Status: production measurements complete.

- 3.1.6 Streamlit runtime regression test: production was observed on unpinned
  Streamlit 1.64.0 while the verified local environment uses 1.58.0. Pin 1.58.0,
  rebuild production, and compare the same deep iframe startup boundaries. If
  startup does not improve or protected behavior regresses, revert the pin.
  Status: rejected. The first 1.58.0 Login took 7.06 seconds, followed by four
  iframe-only traces that never reached the auth component and timed out after
  8.26-8.39 seconds. Production is pinned back to 1.64.0 to prevent drift.

- 3.1.5 Deep iframe startup telemetry: split the embedded Streamlit startup
  gap into component script, component render, browser storage read, callback,
  and final app-ready boundaries. Record production Python, Streamlit, and
  Supabase versions before deciding whether to pin currently floating runtime
  dependencies. Status: implementation ready for production verification.

## Working rule
- A broken core layer must be repaired and validated at its actual integration point. Disabling or bypassing it is not an acceptable primary fix; fallback behavior is only an additional production safety mechanism.
- Every new two-file benchmark cycle starts two fresh instances on separate unused ports and opens both Chrome tabs automatically so `page-23.pdf` and `Металл (1).pdf` can run in parallel under the same code version. Keep older benchmark servers and result screens available for side-by-side comparison; stop them only on explicit request or when resource/port conflicts require cleanup.

## Active
- 3.1.2 Pilot Fast Resume: remove the initial browser-session rerun with a
  30-minute encrypted partitioned resume cookie, retain sessionStorage as the
  compatibility fallback, and keep Supabase as the authority for user and
  company access. Ship disabled first, then verify production enablement,
  fallback, expiry, tamper rejection, and two Sign out / Sign in cycles.
- 3.1.1 Production Observability Foundation: persist correlated browser and
  server timing boundaries without blocking render, changing UI geometry, or
  recording credentials, PII, file names, or RFQ content. Apply the Supabase
  migration and Cloudflare Function secrets before production verification.
- Company Profile follow-up after the v3.0.59 Save Expenses checkpoint:
  diagnose the duplicate heading observed after Sign out, then verify Contacts
  and Company Details remain on their selected tab after Save. Recheck the full
  sign-in, upload, profile, save, logout, sign-in, and reload cycle before
  declaring the checkpoint stable. The Other Spendings migration is applied.
  Do not change the accepted table geometry or the working Expenses save path.
- 3.2.1 Labor Costs: replace the placeholder with an owner-only employee cost
  register. The first production candidate uses one informal `Worker name`
  field, managed Department and Position lists, Monthly Salary or Hourly Rate,
  Average Hours per Month for hourly workers, and a derived Monthly Bruto total. The
  personnel records live in `company_employees`, separately from the Estimation
  `labor` catalog. Net salary, tax, pension, National Insurance, and total
  employer burden remain deliberately out of scope until their calculation
  contract is defined. The initial production version at `b6a3cd8` is an accepted
  rollback point. The current revision moves saved workers above the form, uses
  the Overhead Expenses typography, uses three-column role and hourly rows,
  removes numeric steppers, resets every field after Add, and opens owner-only
  editing from a small pencil beside the worker name. The rejected native-grid
  rewrite was reverted. The pencil is now before the name so edit controls form
  one vertical column. The selector fix targets Streamlit 1.64 React Aria groups,
  inputs, buttons, and option states while retaining the older BaseWeb rules.
  Status: accepted production checkpoint at `1df98c5`; the user confirmed the
  pencil alignment, vertically centered selector text, and purple focus states.
  The current minor candidate removes the extra Add Worker card top margin and
  limits bold disabled styling to calculated text inputs so the disabled
  `Select position` placeholder stays regular weight. Status: accepted
  production checkpoint at `dfcf5ef`; the user confirmed the final spacing and
  selector presentation.
- 3.2.2 Users invitation link: replace the loose heading and code block with the
  existing Users table-card design, keep the owner-only link clickable, and use
  the same compact 12px inter-section gap as Labor Costs. Status: visually
  accepted and pushed at `dff220c`; 186 tests passed.
- 3.2.3 Compact Profile header: remove accumulated Streamlit gaps above the
  visible header, equalize the page-to-title and title-to-tabs spacing at 34px,
  use actual 36px Profile action buttons, align their visual axis with the logo,
  and expose Projects as a disabled placeholder pending its route and data
  contract. Status: visually accepted and pushed at `1f30416`; 186 tests passed.
- 3.2.4 Profile transition compatibility: keep the accepted v3.2.3 action
  alignment and bind the existing Profile-to-Upload transition curtain to the
  stable `profile_to_upload` key instead of visible copy. Status: accepted in
  production as part of v3.2.5.
- 3.2.5 Profile navigation priority: rename the file-workspace action to
  `New Estimate`, keep `Projects` first and `Sign out` last, and prioritize the
  profile tabs as Overhead Expenses, Labor Costs, Price Lists, Contacts,
  Company Details, and Users. Remove the manually maintained build-version
  secret override and enforce matching Streamlit/Cloudflare versions in tests.
  Status: accepted in production at `b372d3d`; 187 tests passed.
- 3.3.1 Authenticated home composition: preserve the accepted Upload logo size
  and position exactly, reduce the three-line product credo, place compact
  Projects, Profile, and Sign out controls between the credo and native upload
  card, and keep Projects visibly disabled until its route exists. Status:
  accepted in production at `cf35d9b`; the full Sign out label is visible, the
  two lower gaps are code-defined at 32px, and 188 tests passed.
- 3.4.1 Company logo normalization: rename the Profile tab to Bank Details and
  add a separate owner-only Company Logo card below Save Contacts. Accept PNG,
  safe self-contained SVG, and first-page PDF sources, normalize them without AI to
  a private 1024px square PNG card, retain only its private Storage reference,
  and instrument conversion, upload, database update, cleanup, and load.
  Status: accepted production checkpoint at `2a6ac0f`; the supplied SVG was
  converted, previewed, saved, and persisted in production, and 203 tests
  passed. Separate PNG and PDF production checks remain pending.
- 3.4.2 Company Logo saved-state UI: hide the empty right-side preview frame,
  keep Drop or Upload available for replacements, align the two-column saved
  composition, use a full-width active Change Logo action backed by the native
  picker, apply the shared 32px Profile action gap, keep drag-over purple, and
  dismiss the success notice after five seconds. Status: accepted in production
  at `32497dc`; 204 tests passed. Closed.
- Profile success-message consistency: move success feedback above Save actions
  across the remaining Profile tabs and use a common dismissal rule without
  changing persistence handlers. Status: deferred to a future block; Company
  Logo already follows the intended placement.
- Auth UI follow-up: improve Sign out press/progress/completion feedback without changing the accepted Sidebar session component, adding JavaScript click interception, `pointer-events: none`, capture handlers, or focus-based infinite spinners. Preserve v3.0.51 refresh persistence and verify two consecutive Sign out / Sign in cycles.
- Unified Detection/OCR experiment sequence — quality first; every step must preserve the stable 3-object and 15-object boundaries before the next step begins:
  1. Make benchmark run IDs unique so repeated runs cannot overwrite prior object results. RFQ OCR uses the V2 rendered-pages route. Naming is text-only and receives locked Detection facts plus OCR snippets, never the PDF again.
  2. Validate the V2 rendered-pages OCR route on `mistral-ocr-4-1`. Mistral retired `mistral-ocr-4-0` on 2026-09-30, which produced `400 Invalid model` in production. Structured vision annotation remains part of the V2 evidence contract. Record OCR completeness, p50/p95, dimensions, tokens, and total time.
  3. Continue the dimensions work already started. Bind every external dimension to the same object index, evidence page, and OCR region; never promote a component size to the whole-object envelope; when axes conflict, return unknown plus a concise clarification instead of guessing. Do not add another full-document pass.
  4. Make Naming text-only. Keep the separate Naming Agent and immutable object list, but stop sending it the PDF again. Pass indices, evidence pages, relevant OCR snippets, and locked Detection facts. Preserve current naming quality and target 2–3 seconds.
  5. Parallelize the first document stage. Start the single Direct PDF OCR request and visual-only commercial object locking at the same time. Join once both finish, then reconcile OCR evidence against the locked object IDs without a second full-document analysis.
  6. Parallelize the post-lock stage. After object IDs and order are immutable, start short Naming and technical OCR enrichment as parallel branches. Neither branch may add, remove, merge, split, or reorder objects.
  7. Completed in v3.0.35: File Review waits only for OCR, Detection, and the authoritative result save. Naming v4 now runs in the background, updates only unchanged provisional names, and no longer blocks the user; full OCR and runtime diagnostics also remain outside the critical path.
  8. Completed in v3.0.40: Processing uses measured Golden stage weights, an ease-in Detection curve, and OCR page-count pacing buckets; the early sprint and slow finish are removed without changing backend work.
  9. Run the acceptance benchmark. Use fresh files and at least three cold runs per file; compare object boundaries, names, dimensions, OCR completeness, p50/p95, tokens, cost, and total user-visible time.
  10. Prepare production concurrency later. Add organization-wide limits, backpressure queueing, 429 handling, and visual-only Detection fallback. Keep one PDF as one OCR request; do not restore per-page fan-out.
- Closed routing experiments:
  - Rendering pages while earlier pages entered OCR produced about 3.5 seconds of overlap on the 11-page file, but is superseded by Direct PDF because the main route no longer renders pages.
  - The 4-versus-6 page-worker experiment is retired. Future concurrency control applies across whole PDF requests from different users, not inside one document.
- Objects Estimation: manual sale price override should stay authoritative after self-cost changes, with manual label and SC-changed notice.
- Add overhead calculation layer after object material/labor pricing.
- Add deterministic delivery and installation pricing from project subtotal / overhead settings.
- Improve catalog matching: save matched material/labor rows and mark weak matches as `needs_review`.
- Run estimation for all detected objects, not only the first object.
- Design Objects Estimation status refresh without Streamlit stale-DOM fragments.
- UI copy: enforce the product rule that the final sentence in a user-facing
  text block has no trailing period. Preserve internal periods and meaningful
  question marks, exclamation marks, and other punctuation. Password recovery
  and shared Auth validation copy now follow this rule; the remaining product
  copy still needs an audit.
- Upload: continue first app/file-load optimization; warm refresh now uses the grey screen/app-ready path, but cold start after reboot can still show one Streamlit skeleton.
- Upload performance follow-up: lazy-load screens and cleanup are done; revisit `.streamlit/config.toml`, cold-start behavior, and optional post-deploy/reboot prewarm.
- Processing: review processing-screen text wording and keep its current position as the layout benchmark.
- Objects Estimation: reduce the large vertical gap between subtitle and pricing table column headers.
- Objects Estimation: add a small blue spinner next to the running Self Cost per Unit percent.
- Objects Estimation: format object quantities as whole units, not 1.0, after estimation completes.
- Objects Estimation: Delivery and Installation should not show Self Cost pending state or Pending review buttons; keep review/status area empty for project-level rows.
- Objects Estimation: keep Delivery and Installation as project-level percentage allocations and show their sale price inputs without fake object status.
- Object Detail: show AI Confidence when available.
- Object Detail: implement Object Preview image capture/display.
- Object Detail to Objects Estimation navigation: remove stale screen fragment flicker on return.
- Object Detail approve action: remove stale screen fragment flicker after clicking Approve.

## Later
- Large-PDF Detection routing: prevent Claude HTTP 413 before starting expensive work. Estimate the complete Messages payload size, including Base64 expansion, OCR context, prompt, and schema; never retry a non-retriable 413 through the fallback model. When the inline payload would approach the 32 MB Messages limit, upload the PDF once through the Anthropic Files API and pass its `file_id` instead of Base64. If the referenced document still exceeds the model context, split it into controlled page groups and reconcile one package-level object set. Persist OCR, upload, Detection, and failure timings for unsuccessful cycles.
- Audit and replace brittle layout code in Objects pricing rows and Upload dropzone when the current estimation/overhead flow is stable.
- Polish negative/error states with project button styles.
- Add XLS proposal export.
- Add missing-object second-pass detection flow.
- 3.7.1 Company Price Sources: retained historical agent/import work, with the
  source-first UI superseded by active task 3.10.1. Production candidate adds one-source upload or
  public-URL ingestion, optional department selection with automatic material-type classification, automatic supplier and
  document classification, unit-preserving normalization, private versioned
  offers, unresolved-row quarantine, source inspection, and private source
  storage. The owner applied the additive database migration before deployment;
  `233 passed` on the production candidate. Verify one photographed invoice and
  one static public supplier page on production. Existing `materials` and the
  current Estimation resolver remain unchanged until import evidence is accepted.
  First production URL test exposed output truncation on the 15k-character
  Rotenberg catalog page; the extraction budget was raised from 8,192 to 32,768
  tokens and explicit max-token failure handling was added. The same page then
  exposed a model arithmetic mismatch, so ready-row normalized prices are now
  calculated deterministically. The final no-write diagnostic completed in
  48.252 seconds with supplier `Rotenberg 1929`, document type `price_list`, and
  48 of 48 rows validated as ready. Production persistence still requires a
  user-visible retest after the hotfix deployment. A later production URL test
  failed before the agent: the page returned only 190 bytes and no readable HTML
  text. Script-only or protected pages now receive a specific instruction to
  upload a PDF, screenshot, or photo. A no-write automatic-category diagnostic
  on the Tsidky page inferred `Sheet Materials`, identified the supplier, and
  validated 39 of 42 rows as ready. Production still needs the exact failing URL
  to determine whether a safe dynamic-page importer is justified. Production
  user testing on checkpoint `4a5fd9a` confirmed that Sign Out no longer reveals
  an unstyled Auth screen and that two automatic-category URL imports completed
  in 22.9 and 9.5 seconds. Both persisted as `partial`, with zero ready prices:
  one returned 27 unresolved rows, the other 6 unresolved and 1 excluded row.
  Price ingestion therefore remains active work, not an accepted completion.
  The preceding session measured Upload to Profile at 3.65 seconds. Its Profile marker
  reached the DOM after 0.68 seconds and its server work was about 0.72 seconds;
  roughly 2.97 seconds were spent waiting for the late general `app-ready`
  component before the Cloudflare transition mask was removed. Checkpoint
  `a626462` reuses the verified styled-target event path for both Upload to
  Profile and Profile to Upload. It verifies screen-specific computed styles before
  revealing either target and leaves the general `app-ready` event unchanged for
  final server-run telemetry. Production trace
  `3ae650ed-7e9e-4b15-b333-3e4691e4c227` measured two Upload to Profile styled
  reveals at 704ms and two Profile to Upload styled reveals at 663ms and 895ms,
  each with one Python run. The user accepted the navigation speed. No further
  transition change is pending unless a new production regression is observed.
