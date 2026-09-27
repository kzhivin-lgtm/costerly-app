# Platform Admin

## 3.13.1 Cross-company dashboard

Status: accepted production checkpoint, closed 27.09.2026.

Protected checkpoint: `d8e0c8e`.

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
- Dollar signs appear beside monetary values, not in the column headings.
- Cloudflare masks Upload/Profile/Admin transitions until the target screen's established heading and content geometry are ready.
- PDFs display `—` until proposal generation and Projects persistence exist.

### Applied release

1. Applied `db/sql/2026_09_27_platform_admin_dashboard.sql` and the corrected dashboard RPC for legacy timestamps.
2. Applied `db/sql/2026_09_27_platform_admin_sessions.sql`; session telemetry now starts from deployment and does not infer historical sessions.
3. Granted explicit Platform Admin access to the two approved trusted accounts.
4. Deployed the application through `d8e0c8e`, including the final stale Upload-frame transition fix.
5. Verified the live dashboard RPC, production company aggregates, rolling session counts, agent costs, and successful Railway deployment. The owner accepted the production matrix and closed the task.

### Verification contract

- Platform Admin sees the Admin action and one aggregate row per company.
- Company Admin and Team Member do not see the action.
- A direct Admin route is rejected unless the user has active `platform_staff` access.
- Company Admin remains protected from removal despite the user-facing role rename.
- Costs use tracked US dollars with two decimal places in every column.
- Unknown cost and unavailable PDF data are visibly distinguished from zero.
