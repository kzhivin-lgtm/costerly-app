# Platform Admin

## 3.13.1 Cross-company dashboard

Status: first production checkpoint deployed; unfiltered matrix revision implemented locally and awaiting deployment and production acceptance.

Protected checkpoint: `193713e`.

### Decisions

- Company authorization remains `owner/member` in the database and code. The interface displays those roles as `Company Admin/Team Member`.
- Cross-company access is independent and explicit through `platform_staff`. Company registration and company roles never grant Platform Admin access.
- The first dashboard is read-only and has no company detail page.
- The first dashboard is one unfiltered all-time company matrix. Sessions retain explicit rolling 7-day and 30-day windows inside the table.
- The matrix reuses the compact table geometry established by Overhead Expenses. Rows are not interactive until the company detail task is approved.
- Dashboard rows expose company-level aggregates only. They do not expose file names, source content, prompts, or extracted customer data.
- Account stage is an internal `test/pilot/paid` classification.
- Sessions are distinct authenticated Streamlit runtime sessions started within rolling 7-day and 30-day windows. Reruns inside one runtime session are deduplicated.
- Session history begins when this telemetry is deployed. Earlier sessions cannot be reconstructed from existing data.
- Exact same-file reuploads are identified with a company-scoped SHA-256 fingerprint. The raw file is not stored in analytics metadata.
- Detection cost groups OCR, Detection, and Naming. Estimation counts per-object calls. Price Lists counts Price Source calls.
- AI costs use one display unit: tracked US dollars with two decimals. An entirely unpriced cost is shown as unavailable, never as a known zero.
- PDFs display `—` until proposal generation and Projects persistence exist.

### Release order

1. Apply `db/sql/2026_09_27_platform_admin_dashboard.sql`.
2. Grant one existing trusted account with `tools/grant_platform_access.py`.
3. Optionally classify companies with `tools/set_company_stage.py`.
4. Deploy the application code.
5. Run authenticated production acceptance for Platform Admin, Company Admin, Team Member, and a direct unauthorized Admin route.

### Verification contract

- Platform Admin sees the Admin action and one aggregate row per company.
- Company Admin and Team Member do not see the action.
- A direct Admin route is rejected unless the user has active `platform_staff` access.
- Company Admin remains protected from removal despite the user-facing role rename.
- Costs use tracked US dollars with two decimal places in every column.
- Unknown cost and unavailable PDF data are visibly distinguished from zero.
