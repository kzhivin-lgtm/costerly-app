# Costerly Architecture

Costerly Streamlit should stay a thin UI shell.

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
For now, both blocks intentionally produce the same light Costerly UI. This lets us add a real dark theme later by changing dark tokens without rewriting screens.
The app should not follow Streamlit native dark mode yet.

Company Profile UI and persistence contract
Company Profile owns its local page heading and navigation actions. The shared
full Costerly logo and global Profile action are not rendered on that screen.
The page uses six peer tabs: Overhead Expenses, Labor Costs, Price Lists,
Contacts, Bank Details, and Users. Overhead Expenses is first. Contacts and Bank
Details submit independently.
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
Contacts form. Owners may submit PNG, self-contained SVG, or the first page of a
PDF, up to 50 MB. A deterministic server pipeline validates the actual content,
rejects active or externally referenced SVG content, trims empty margins,
preserves proportions, and places the artwork inside a 1024 by 1024 white PNG
card with the shared contour. Raster PNG artwork below the minimum usable
resolution is rejected rather than invented or AI-upscaled. Source bytes are
never stored. Only the normalized PNG, capped at 2 MB, is written to the private
`company-logos` Supabase Storage bucket. `companies.logo_url` retains the
server-only `storage://company-logos/...` reference. The server uploads a new
unique object, updates the company row, rolls the object back if that update
fails, and removes the prior normalized object only after success. Members may
view the server-loaded normalized logo but cannot upload one.
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
The `2026_09_19_company_employees.sql` migration has been applied to the live
Supabase schema.
The Users tab renders the owner-only team invitation URL with the same
`company-profile-users` table-card primitive as the member list. It is a real
link, not a code block, and uses a 12px section gap so the two related tables
read as one compact group. Non-owners do not receive or render the invitation
URL.
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
