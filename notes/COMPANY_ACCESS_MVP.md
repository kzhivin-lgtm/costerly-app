# Company access MVP

## Accepted scope

- One company may have multiple users. A user belongs to one company.
- The company creator is its single owner. Every user joining with the reusable
  link is a member. Both can create/use RFQs and estimates. Only the owner may
  change company-wide metrics and price-list settings when those screens land.
- The pilot operator generates exactly one one-use company-creation link per
  counterparty, manually. Links have no expiry and are not email-bound. Both
  owner and employee links always use `https://app.costerly.ai/`; local
  shared links are rejected.
- One-use owner links use `/start/<token>`. Reusable employee links use
  `/join/<token>`. No company ID or email appears in either URL.
- The operator command generates two secrets at once. It returns only the
  one-use owner-registration URL. The future reusable staff token is stored
  server-side with that invitation, attached to the company atomically when
  the owner registers, and shown in Company Profile only to the owner.
- Opening a valid token on localhost may display the form for UI development,
  but submission is rejected before any Auth user, company, or membership is
  written. Both real registration paths must run through the public app.
- Email/password is only the account login. Confirm Email is intentionally
  bypassed only for invited registrations in the controlled MVP. The global
  Supabase Auth setting remains unchanged.
- Registration/contact email requires a public-email shape such as
  `name@company.com` or `name@company.com.ai`. This is syntax validation only;
  neither DNS nor mailbox ownership is checked in this pilot.
- Company Profile initially has four sections: company details, metrics, users,
  and price lists. Only company name/contact email/phone are editable now.
  Pricing metrics and price-list uploads remain subsequent tasks.
- Existing Detection and Estimation benchmarks stay on the legacy path until
  the company-auth rollout is verified.

## Task queue

| Priority | Status | Task | Trigger |
| --- | --- | --- | --- |
| P0 | Active | Access code and SQL migration | Complete local checks |
| P0 | Pending | Current-project SQL/Auth activation and two-company verification | Local checks and public URL |
| P1 | Pending | Confirm Email and production SMTP | Before email recovery or verified accounts |
| P1 | Pending | Pilot-friendly login persistence | Decide Streamlit stopgap versus React |
| P1 | Active | Company Profile first screen and contacts | Manual UI review after registration |
| P1 | Pending | Pricing metrics and requisites/logo onboarding | Profile first screen accepted |
| P1 | Pending | Company price-list library and shared fallback | Pricing onboarding contract |
| P2 | Pending | Estimation Agent improvement | Trusted company inputs |

## Implemented locally

- Supabase email/password sign-in and server-side invitation-gated admin
  registration. Admin create_user sends no confirmation email, so the existing
  project-wide Confirm Email setting does not need to be disabled.
- Live-schema check: `companies` has `company_name`, `public_email`, and
  `public_phone`. The strict additive account tables and two invitation RPCs
  have been applied by the user; the later security-policy cutover has not.
- Server-side company creation and membership resolution.
- Existing `companies_id_format` accepts only three numeric characters. New
  company IDs follow that format; transactional RPC calls retry on unique-key
  collisions. The current schema has a 999-ID ceiling and will need a planned
  migration before broad self-service signup.
- A failed company creation after Auth signup leaves the invite unused and the
  user without membership. The same creation form tries the existing login
  first and completes the company if the password matches; it only creates a
  new Auth user when login fails because credentials are unknown. No existing
  Auth user is deleted automatically.
- A one-owner-per-company database constraint and a server-side owner guard for
  company-wide writes. The first Profile editor saves only name and contact
  email/phone. Company creation routes to Profile once; later login routes to
  Upload.
- A trusted command creates exactly one manual one-use company link. Only its
  SHA-256 hash is stored. Creation and consumption happen in one SQL transaction.
- Each company gets a permanent random join token automatically at creation.
  It is kept in a server-only table so members can copy it later. Joining is
  not tied to email and does not consume the link.
- The Cloudflare iframe wrapper forwards only the opaque invitation token to
  Streamlit; there is no company ID or email in the public URL.
- An app-level ownership gate on deep links and selected RFQ/estimate IDs.
- Ownership checks before File Review reads/edits and server-side Estimation,
  Object Detail, and pricing reads/writes, including queued background edits.
- Server-generated RFQ run IDs in company mode, avoiding cross-company upserts
  under a model-generated duplicate ID.
- The Objects browser runtime uses the authenticated user's JWT in company
  mode. The service-role key stays on the Streamlit server.
- A migration that revokes anonymous access to pricing overrides and the
  progress/cost view, then applies authenticated company-member policies.

## Atomic rollout, not yet performed

1. Configure `COSTERLY_PUBLIC_URL=https://app.costerly.ai/`. The existing Supabase `Confirm Email`
   setting stays on; the invited registration path creates accounts through
   a server-only admin call and signs them in immediately. Those addresses
   are not verified, so do not treat them as proof of identity. Password
   recovery still requires an email configuration later.
2. Apply `db/sql/2026_09_15_company_access_stage1_strict_additive.sql` first.
   It adds only three new account/invitation tables and leaves the legacy
   runtime intact. Do not run the earlier SQL pasted in chat.
   Then apply `2026_09_15_company_access_stage2_invite_rpcs.sql`, which adds
   only the two invitation functions. The later security cutover in
   `2026_09_15_company_access_foundation.sql` removes the anonymous endpoints
   and must be coordinated with app activation.
3. Deploy the code and set `COMPANY_AUTH_ENABLED=true` in server-side secrets.
   It defaults to false so the last accepted benchmark path is unchanged.
4. Generate one company-creation link with
   `tools/create_company_creation_link.py`. Verify registration, company
   creation, automatic join link, two or more employees using the same link,
   login, logout, direct deep links, and two-company data isolation.
5. Confirm anonymous REST requests can no longer read pricing overrides or
   object-estimate progress, and can no longer write pricing overrides.

## Known MVP limits

- Streamlit session state does not persist login across a full browser refresh.
  This needs a deliberate session-persistence decision, or may be solved in the
  planned React migration, before inviting external pilot users.
- Production login UI and invitation ergonomics need an end-to-end browser
  review. A leaked company join link stays valid until rotation is added.
- Membership revocation while a background Estimation job is already running
  does not cancel that job. There is no membership-management UI in this MVP.
- The creator's Auth account cannot be deleted while its membership exists.
  An owner-transfer/recovery flow is needed before account deletion or
  self-service role management is introduced.
