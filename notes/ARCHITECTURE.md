# Costerly AI Architecture

Costerly AI Streamlit should stay a thin UI shell.

```text
Streamlit UI
  screens / ui / styles
        ↓
Application use cases
        ↓
Services
        ↓
Supabase / Anthropic / file parsing
Rule
Screens receive user actions and render state. They do not own business logic.
Theme Policy
The design system has light and dark token blocks.
For now, both blocks intentionally produce the same light Costerly AI UI. This lets us add a real dark theme later by changing dark tokens without rewriting screens.
The app should not follow Streamlit native dark mode yet.

Company Profile UI and persistence contract
Company Profile owns its local page heading and navigation actions. The shared
full Costerly AI logo and global Profile action are not rendered on that screen.
The page uses seven peer tabs: Overhead Expenses, Labor Costs, Machinery, Price
Lists, Contacts, Bank Details, and Users. Overhead Expenses is first. Contacts
and Bank Details submit independently.
Their save handlers send partial company updates, so a field hidden from the UI
is not converted to null. In particular, the retained VAT file number and
country values remain unchanged until a deliberate data-migration decision.
Every editable Profile form renders its submit action through the shared
`_profile_save_button` helper. Profile form submits use the same full-width,
high-emphasis purple design regardless of the current or future tab.
Bank Details is the single editing surface for company identity and banking
data. Its five-row grid keeps Company name and registration together, both legal
names together, then Bank name / Bank number, Branch number / Account number,
and IBAN / BIC. BIC continues to use the existing `swift` database column because
SWIFT/BIC is one banking identifier, so no duplicate column is introduced.
Contacts also owns a separate Company Logo card below its independent Save
Contacts form. Owners may submit PNG, safe self-contained SVG, or the first page
of a PDF, up to 50 MB. A deterministic server pipeline validates the actual
content, strips standard SVG 1.1 DOCTYPE declarations, accepts embedded
PNG/JPEG/WebP artwork, rejects active or externally referenced SVG content, trims empty margins,
preserves proportions, and places the artwork inside a 1024 by 1024 white PNG
card with the shared contour. Raster PNG artwork below the minimum usable
resolution is rejected rather than invented or AI-upscaled. Source bytes are
never stored. Only the normalized PNG, capped at 2 MB, is written to the private
`company-logos` Supabase Storage bucket. `companies.logo_url` retains the
server-only `storage://company-logos/...` reference. The server uploads a new
unique object, updates the company row, rolls the object back if that update
fails, and removes the prior normalized object only after success. Members may
view the server-loaded normalized logo but cannot upload one.
The owner card keeps the native Drop or Upload surface available for both first
save and replacement. A saved or newly selected logo renders in the right-hand
preview; no empty preview is rendered before the first selection. The same
full-width action reads Save Logo for the first object and Change Logo when a
stored reference exists. In the idle saved state a Sidebar-hosted browser guard
uses the active Change Logo click only to open the native picker. Once a valid
replacement is pending, the click reaches the normal owner-validated server
save. The hidden state markers and guard component never participate in page
layout. Logo drag-over is forced to the shared purple focus treatment.
`--profile-action-gap` is the 32px design-system token for the final visible
content-to-full-width-action rhythm, derived from the accepted Contacts layout.
Company Logo uses it above and below the upload/preview composition.
Overhead Expenses reuses the existing `overhead_settings` and
`overhead_monthly` records. Its save path is owner-only and updates only the fields visible on the Metrics
screen, preserving other overhead settings. Monthly overhead values are stored
as whole shekels. One company VAT percentage applies to taxable overhead rows;
Arnona is VAT-exempt in the Metrics breakdown. VAT and Total are deterministic
derived values, never editable inputs. The same stored VAT percentage is used
for project and object pricing totals instead of a hard-coded 18 percent rate.
`other_spendings_cost` is the shared catch-all monthly overhead field for
Overhead Expenses and deterministic Object Detail allocation. The versioned
`2026_09_18_other_spendings_overhead.sql` migration has been applied to the live
Supabase schema.
Labor Costs stores owner-only worker compensation in `company_employees`, never
in the Estimation `labor` catalog. The first contract uses one informal Worker
name, controlled Department and Position values, and either Avg Monthly Bruto or
Hourly Rate plus integer Average Hours per Month. Monthly Bruto is derived rather
than stored. Each worker can be edited through the same owner-only validation
path. Net salary and statutory employer-cost calculations remain out of scope.
The compact summary table uses table-only `Hourly` and `Monthly` labels and
omits the employment factor from Pay Details because the Monthly result already
contains it. Selector labels are intentionally bounded for table layout:
`Painter`, `Worker`, `Designer`, and `Carpenter` replace longer variants.
Retired position codes remain readable and are never rewritten by presentation
changes.
The `2026_09_19_company_employees.sql` migration has been applied to the live
Supabase schema.
Machinery is an additive production-capability boundary. The global
`machinery_catalog` defines a compact furniture-production vocabulary. Company
answers live in `company_machinery`; regular subcontractor capabilities reuse
`company_suppliers` through `company_supplier_services`; price evidence and
regional fallbacks have separate versioned tables. The prototype
`company_machines` table remains untouched and is not a source of truth for the
new UI. Owners edit one idempotent company/machine identity, members receive a
read-only view, and changing an in-house capability to unavailable requires
confirmation. Removing a regular subcontractor deactivates the routing choice
without deleting its history. `use_cases/machinery.py` validates the catalog,
capabilities, pricing semantics, ownership, and constructs a bounded production
snapshot. That private snapshot is not passed to an external model without an
explicit data-transfer decision. Deterministic application code remains the
owner of feasibility checks and price arithmetic.
The `2026_09_24_machinery_foundation.sql` migration was applied to the live
Supabase schema on 24.09. The seeded catalog contains 26 active capabilities;
company-specific Machinery tables begin empty. Anonymous access is revoked.
The Users tab does not retain or reveal a permanent team URL. An owner action
creates a fresh opaque bearer invitation, stores only its SHA-256 hash in
`company_member_invites`, and shows the raw link in the existing
`company-profile-users` table-card primitive. The owner surface deliberately
renders the URL as non-navigable text with a browser-native Copy action, so the
owner can forward it without opening it under the current authenticated session.
The link is not email-bound,
expires after 24 hours, and is consumed in the same database transaction that
creates the first member relationship. Row locking prevents concurrent reuse.
The owner may remove a member after explicit confirmation. That operation
deletes only the `company_members` relationship; it never deletes the Auth user,
and the owner relationship is protected in both application and database code.
The legacy `company_join_links` table is retained only as a rollback surface.
Non-owners cannot create invitations, see generated links, or remove members.
The public Join registration is an auth-screen variant, not a separate design
system: it shares the Sign in heading treatment, form width, full-width primary
action, field validation, immediate spinner, and retained-screen transition.
The Company Profile header removes top-level zero-height CSS and screen-marker
wrappers from layout flow so Streamlit's vertical gap cannot accumulate above
visible content. The page and heading-to-tabs gaps are both 34px. Header actions
use a real 36px compact-button override, align with the title's visual axis, and
show Projects as an intentionally disabled placeholder until a project-history
route and persistence contract exist.
The Overhead Expenses cost table and Object Detail tables share the same
`object-detail-table`, row, cell, group-summary, and cell-input CSS primitives.
Do not rebuild Metrics cost rows with `st.columns` or native `st.text_input`:
their framework wrappers have independent minimum heights and break the shared
grid geometry. Metrics uses editable HTML only for Monthly Cost and recalculates
derived VAT and Total in its isolated browser guard. A zero-height Streamlit
component captures the Save Expenses action and returns one serialized snapshot
to an `st.fragment`, without URL navigation or a full-page query-parameter
submission. The server rechecks company ownership, updates an existing
`overhead_settings` or `overhead_monthly` row without nulling hidden columns,
and inserts a complete default-backed row only when the company has no row yet.
All Profile text inputs reuse the Sign in input geometry and focus contract:
neutral default border, purple focus ring, no red focus-only state, and no
framework keyboard instruction. Auth and Upload styling remain separate
protected surfaces.
Profile selectboxes support both the older BaseWeb Select DOM and the Streamlit
1.64 React Aria ComboBox DOM. React Aria control groups own the 52px outer
geometry and purple focus ring; their 50px input and button children must not
overflow the group. Disabled select placeholders keep regular font weight.
Bold disabled styling is limited to calculated text inputs.

SQL migration safety rule
Before a SQL migration is handed to the user, inspect the complete final query
for `DROP`, `DELETE`, `TRUNCATE`, cascading foreign-key actions, destructive
`ALTER`, privilege changes, RLS effects, and repeat-run behavior. Remove any
destructive operation that is not required. Explicitly state the remaining data
and access impact instead of relying on the SQL editor warning.

Auth browser-session boundary
Supabase access and refresh tokens are mirrored into tab-scoped browser
`sessionStorage` so a full refresh can restore the authenticated Streamlit
state. The browser bridge is a zero-height custom component rendered only in
the hidden `st.sidebar`. It must not be mounted in the main block container,
because component iframes participate in Streamlit layout and can move accepted
screen geometry even when no screen CSS changes. The component reads storage
only during Streamlit-session bootstrap. Store and clear commands do not return
a component value, because that callback would schedule a rerun capable of
consuming the next button or form interaction. Sign out and invalid-token
handling clear both Streamlit state and browser session storage. `localStorage`
is intentionally not used, so closing the tab ends this browser-held session.

The Cloudflare transition mask may reveal the Sign In screen only after the
rendered auth form satisfies its computed-style contract. DOM presence alone is
not readiness because Streamlit can insert the form before the Auth stylesheet is
applied. The current contract checks the auth marker and brand plus the form's
20 px radius and 30 px padding, then waits two animation frames before emitting
`app-ready`. A bounded fail-open prevents the wrapper from remaining masked if
the Auth CSS contract changes unexpectedly, and telemetry records whether the
style check succeeded and how long it waited. During masked Sign Out, Upload to
Profile, and Profile to Upload transitions, the transition observer applies a
screen-specific computed-style contract and lets the wrapper reveal the completed
target immediately, without waiting for a newly mounted Streamlit component to
relay the later general `app-ready` event. The general event remains the final
server-run and telemetry boundary.

Interface scenario contract boundary
Every interactive screen is specified through an owner-approved scenario
matrix before layout or behavior changes begin. The matrix is the shared
contract between product behavior, field validation, browser interaction code,
server outcomes, automated regression tests, and production acceptance. It
must include empty and partial forms, local and server validation, progress,
success, error, retry, duplicate submission, keyboard behavior, navigation,
mobile behavior, and protected surrounding flows. New behavior discovered
during testing changes the matrix first; it must not be patched as an isolated
visual exception. A screen becomes a checkpoint only after the implemented
matrix and the real production surface agree.

Responsive Policy
Every screen should be designed for desktop and mobile from the start.
For each screen, define:
desktop layout;
mobile layout;
what changes at max-width: 760px;
what must not shift or overlap.
RFQ Processing Target Flow
uploaded file accepted by Streamlit
        ↓
process_uploaded_rfq()
        ↓
parse file metadata/content
        ↓
run Mistral OCR once and normalize page text/structure
        ↓
run detection agent
        ↓
validate and normalize detection result
        ↓
persist RFQ run and detected objects
        ↓
render review screen
Comments
Code comments should explain responsibility and timing:
why a module exists;
when a function is called;
what the function deliberately does not do.
Avoid comments that repeat obvious code.
MD
```

OCR Runtime v1
The upload flow calls Mistral OCR 4 before Detection. OCR returns a provider-neutral
page package with Markdown, page dimensions, blocks, tables, images, and confidence.
Detection still receives the original visual file and uses compact page-numbered OCR
text as additional evidence. The OCR package is kept in Streamlit session state for
the current run; durable Supabase caching and object-specific Estimation contexts are
future steps.

Detection Prompt v3 Candidate
Detection uses the contractor quotation line as its commercial object boundary. It
separates physically independent products, merges repeated views and integral
components, preserves object-level indices, and returns compact names, complete-unit
quantities, external W × H × D dimensions, materials, evidence pages, and short
actionable notes. Sheet and room titles are context, never object names. Detection
prepares the Estimation handoff but does not create BOM, labor, or pricing output.

Estimation Target Flow
confirmed detected objects
        ↓
start_estimation_for_run()
        ↓
create pending estimate + object estimate records
        ↓
future Estimation Agent fills material/labor/overhead lines per object
        ↓
deterministic calculation engine totals costs, VAT, and sale prices
        ↓
Objects Estimation and Object Detail render persisted estimate state
Rule
The Estimation Agent proposes line items and quantities. It does not own final arithmetic totals; deterministic engine code owns multiplication, VAT, totals, delivery, installation, and proposal math.

Estimation Agent Contract v1
The Estimation Agent runs per object. It may return material composition, material quantities, labor work types, and labor hours.
It must not return material unit costs, labor rates, overhead rows, VAT, self-cost totals, sale prices, or final proposal totals.
Each material row must explain quantity through `quantity_basis`, `evidence_pages`, `confidence`, and `notes`.
Each labor row must explain hours through `hours_basis`, `evidence_pages`, `confidence`, and `notes`.
`catalog_match_query` is a search hint for matching the agent line to company material catalog rows; it is not a price.
Deterministic engine code owns catalog matching, prices, rates, overhead allocation, multiplication, VAT, and totals.

Company Price Sources contract (3.7.1)

Price Lists accepts one logical document or one public URL per operation. One
logical document may be one file or an ordered set of JPEG/PNG photographs,
which deterministic preprocessing combines into one private PDF source before
agent extraction. The owner may choose the department or leave it for automatic
classification. Supplier identity, document type, document number, document date,
price context, currency, VAT basis, subtotal, VAT amount, final total, product
rows, units, package quantities, and conversions are inferred by the import
pipeline. Each product row owns its Material Type because a single commercial
document may contain materials from several departments. The default path never
asks the owner to verify rows. A source and every extracted row remain
inspectable after processing.

The model has no database access. It returns a validated extraction package.
Deterministic code enforces supported file types, public-only URL fetching,
non-negative values, currency presence, explicit conversion evidence, unique row
numbers, and an auto-activation confidence floor. Ambiguous rows are persisted as
unresolved and never become active offers. Delivery, assembly, labor, credits,
subtotal rows, VAT or tax total rows, grand totals, and amounts due are excluded
as non-product rows. Their presence never causes VAT to be added to or removed
from an extracted item price. Every item retains the VAT basis shown by its source.
When explicit subtotal, VAT, and total values do not reconcile, deterministic
code reduces row confidence and records `document_total_mismatch`. A mismatch
between a user-selected department and an extracted row makes that row
unresolved instead of aborting or silently reclassifying the complete source.
For ready rows, deterministic code calculates `normalized_price` from the model's
evidenced `raw_price` and `conversion_factor`; a conflicting model calculation is
replaced and recorded with `normalized_price_recalculated`.

The source value and unit are retained separately from `purchase_unit`,
`calculation_unit`, `conversion_factor`, and the normalized Estimation price.
Aliases such as `sqm`, `m2`, `m^2`, `m²`, and supported language equivalents
normalize to `m2`, while the exact source spelling remains evidence. A conversion
is allowed only when every required package size,
length, volume, count, or sheet dimension is explicit in the source. Company
materials begin private. Repeated private evidence may later propose a country
catalog identity, but company prices, discounts, and purchasing terms remain
private. Existing scraped materials remain an unverified benchmark until a later
resolver task explicitly changes pricing precedence.

Byte SHA-256 rejects an identical upload before agent processing. A semantic
document fingerprint also rejects the same numbered supplier document when it
is uploaded as another file or photograph. Source Details renders stored ISO
dates as MM/DD/YY and exposes document totals, per-row Material Type and VAT,
agent duration, and compact TC without a currency sign. Provider-reported token
usage, configured cost, model, and prompt version remain stored for audit.

Price Catalog UI contract (3.10.1)

The primary Price Lists presentation reads active `company_material_offers`
joined to normalized `company_material_items`, supplier, source-row, and source
provenance. It groups offers by the user-facing `Wood`, `Metal`, and `Finishing`
departments and department-specific material types. Add Source accepts only an
optional department, while the extraction agent infers the narrowest material
type. The catalog exposes Department, Material Type, and Supplier filters;
Search is intentionally omitted from this compact revision. Source documents remain
in a separate private library. A catalog row never replaces or discards source
evidence. Foreign-currency offers retain their actual currency until a verified
ILS conversion exists; presentation code must not relabel them as shekels.
The owner accepted this presentation at checkpoint `d18b533` on 25.09.2026.
Subsequent Price Source Agent accuracy work resumed as task 3.12.1 after the
3.11.1 Legal block. The owner explicitly approved the Source Details metadata,
Material Type, VAT, timing, and TC additions. Other accepted UI geometry remains
protected unless a new interface decision is explicitly approved.

Estimation Agent Runtime v1
`estimate_one_object()` is the application-layer entrypoint for one object.
It loads the detected object from Supabase, calls the Estimation Agent with the original uploaded file bytes, validates the returned JSON, replaces that object's estimate lines, and records an `agent_usage_events` row with `agent_name = estimation`.
The UI does not call Anthropic directly.

Agent Runtime Metrics v1
The user-facing Elapsed timer starts when a file is selected, appears immediately
inside the upload processing shell, and continues monotonically across the real
Processing screen without resetting or competing with server-rendered timer values. File Review shows OCR, Detection, and total cycle seconds.
`agent_usage_events` records OCR, Detection, Estimation, and orchestration durations;
`raw_usage.duration_seconds` remains the backward-compatible source until the explicit
duration column migration is applied.

Production Runtime Observability v1
The Cloudflare wrapper creates one `trace_id` per outer-page load and passes it
to the embedded Streamlit URL. Streamlit retains one `session_id` across Auth
transitions and creates one `run_id` for every Python rerun. Browser and server
events use the shared `app_runtime_events` schema. Browser writes go through a
same-origin Cloudflare Pages Function; server writes use a bounded background
queue. Telemetry is best-effort, cannot block rendering, and contains no
credentials, email addresses, file names, uploaded content, prompts, or RFQ
content. `notes/OBSERVABILITY.md` is the authoritative event and deployment
contract.

Railway Hosting Topology v1
`app.costerly.ai` remains the production Cloudflare Pages wrapper and embeds
`https://costerly-app-staging.up.railway.app/?embed=true`. The same wrapper
served at `staging.costerly.ai` selects that Railway backend explicitly. The Railway-generated
hostname is an infrastructure endpoint, not a user-facing product address.
Cloudflare owns the loading and transition mask, route synchronization, branded
origin, and browser telemetry endpoint. Railway owns the Streamlit process and
its runtime variables. GitHub remains the deployment source. The prior
Streamlit Cloud deployment is retained temporarily as the rollback backend
until the Cloudflare plus Railway transition sequence is accepted.

Python production dependencies use `pyproject.toml` plus the committed
`uv.lock` as the single source of truth, with Python pinned by
`.python-version`. Railpack 0.39.0 detects this layout and runs uv for both
dependency and project synchronization. `requirements.txt` must not be added
alongside the lock file because this Railpack version gives it precedence and
falls back to pip. Streamlit Community Cloud also recognizes `uv.lock`, so the
rollback deployment remains supported without a second dependency manifest.

The owner accepted this topology in production on 2026-09-22. Streamlit Cloud
is no longer the active iframe backend, but remains available temporarily for a
direct wrapper rollback. The browser-facing application URL remains
`https://app.costerly.ai`; Railway service URLs are infrastructure-only.

Pilot Fast Resume v1
For the early-bird Streamlit release, an optional 30-minute Fernet-sealed
resume blob may be stored as a `Secure`, `SameSite=None`, `Partitioned`,
host-only cookie. It contains only the existing Supabase session needed to
avoid the initial browser component rerun. Supabase still validates the user
and company membership on every new Streamlit session. The existing
sessionStorage transport remains the compatibility fallback. The feature is
disabled unless `COSTERLY_FAST_RESUME_ENABLED` and a valid
`COSTERLY_SESSION_SEAL_KEY` are both configured. Cookie contents, tokens, and
decrypt errors must never be written to runtime telemetry.

Pricing Runtime v1
`price_estimated_object()` is the deterministic pricing entrypoint after one object is estimated.
It reads the object's persisted material/labor lines, matches materials to the `materials` catalog, matches labor roles to the `labor` table, fills `unit_cost`, `rate`, and `cost`, then updates object self-cost totals.
This layer owns arithmetic. The Estimation Agent remains responsible only for composition, quantities, labor hours, and reasoning.

Legal Consent and Verified Registration v1
The feature is cross-system and active by default after the private-playground
version 1.0 rollout. `LEGAL_CONSENT_ENABLED=false` remains the server-side
rollback switch.
Invitation signup resolves immutable published Terms and Privacy releases,
requires the Terms checkbox in the first and only registration form, creates an
unverified Supabase user, and records a server-side pending registration plus
append-only acceptance evidence. Email confirmation returns a verified session
through the existing Cloudflare wrapper and hidden browser-session component.
Only then does one database transaction consume the saved invitation and
create the company or membership. Returning users authenticate before any
legal-state lookup. Their verified `user_id`, not typed email, is checked
against the current Terms acceptance version before company data renders.
Privacy-only releases do not create a gate. Published document rows and legal
evidence cannot be edited or deleted. The mutable release pointer selects the
current immutable document. The frozen pre-launch legal-text checkpoint uses
Terms 1.3 with acceptance version 4 and response SHA-256
`346cb5ee4be1cac1b0fa4a80deb8c1a89a330e426dae8d931485b79233cc2b0d`,
plus Privacy 1.2 with unchanged acceptance version 1,
`requires_reacceptance = false`, and response SHA-256
`baee97a79a3be012dec6b0e5610aa380abd01e753dd64930ea97ec25bf13d674`.
See
`notes/LEGAL_CONSENT_VERIFIED_REGISTRATION.md` for the scenario and rollout
contract.
