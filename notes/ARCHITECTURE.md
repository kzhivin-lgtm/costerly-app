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

Pricing Runtime v1
`price_estimated_object()` is the deterministic pricing entrypoint after one object is estimated.
It reads the object's persisted material/labor lines, matches materials to the `materials` catalog, matches labor roles to the `labor` table, fills `unit_cost`, `rate`, and `cost`, then updates object self-cost totals.
This layer owns arithmetic. The Estimation Agent remains responsible only for composition, quantities, labor hours, and reasoning.
