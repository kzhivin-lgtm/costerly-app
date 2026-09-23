# Company access MVP

## Accepted scope

- One company may have multiple users. A user belongs to one company.
- The company creator is its single owner. Every user joining with a one-time
  team invitation is a member. Both can create/use RFQs and estimates. Only the owner may
  change company-wide metrics and price-list settings when those screens land.
- The pilot operator generates exactly one one-use company-creation link per
  counterparty, manually. Links have no expiry and are not email-bound. Both
  owner and employee links always use `https://app.costerly.ai/`; local
  shared links are rejected.
- One-use owner links use `/start/<token>`. One-use employee links use
  `/join/<token>`. No company ID or email appears in either URL.
- The owner generates a fresh employee invitation in Company Profile. Its raw
  bearer token is shown only after generation, is not email-bound, expires in
  24 hours, and is consumed atomically by the first successful registration.
- Opening a valid token on localhost may display the form for UI development,
  but submission is rejected before any Auth user, company, or membership is
  written. Both real registration paths must run through the public app.
- Email/password is only the account login. Confirm Email is intentionally
  bypassed only for invited registrations in the controlled MVP. The global
  Supabase Auth setting remains unchanged.
- Registration/contact email requires a public-email shape such as
  `name@company.com` or `name@company.com.ai`. This is syntax validation only;
  neither DNS nor mailbox ownership is checked in this pilot.
- Company Profile has six peer sections: General, Contacts, Bank Details,
  Metrics, Users, and Price List. Owners can edit the current general, contact,
  address, social, and bank fields. Pricing metrics and price-list uploads
  remain subsequent tasks.
- Existing Detection and Estimation benchmarks stay on the legacy path until
  the company-auth rollout is verified.

## Task queue

| Priority | Status | Task | Trigger |
| --- | --- | --- | --- |
| P0 | Completed | 3.8.4 one-time team invitations and member access removal | Accepted in production on 22.09 |
| P0 | Active | 3.8.2 password recovery | Verify Supabase recovery mail transport and redirect contract |
| P1 | Completed | 3.8.5 Railway GitHub autodeploy reliability and build timing | Automatic deployment and uv build verified at `bf0581d`; Railway completed in 193 seconds |
| P0 | Pending | Current-project two-company verification | Dedicated cross-company acceptance pass |
| P1 | Pending | Confirm Email and production SMTP | Before production recovery email delivery or verified accounts |
| P1 | Completed | Tab-scoped login persistence | Accepted v3.0.51 checkpoint |
| P1 | Completed | Company Profile first screen, contacts, and bank details | Accepted v3.0.49 checkpoint |
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
  company-wide writes. Profile sections submit partial updates so hidden VAT
  and country values are preserved. Company creation routes to Profile once;
  later login routes to Upload.
- A trusted command creates exactly one manual one-use company link. Only its
  SHA-256 hash is stored. Creation and consumption happen in one SQL transaction.
- The owner confirmed the additive migration was applied on 22.09. It introduces server-only, one-time team
  invitations and atomic consumption. The application stores only the token
  hash, rejects used or expired links, and lets the owner remove a member's
  company relationship without deleting the Auth account. The production
  rollout and owner acceptance were completed on 22.09.
- The Cloudflare iframe wrapper forwards only the opaque invitation token to
  Streamlit; there is no company ID or email in the public URL.
- An app-level ownership gate on deep links and selected RFQ/estimate IDs.
- Ownership checks before File Review reads/edits and server-side Estimation,
  Object Detail, and pricing reads/writes, including queued background edits.
- Server-generated RFQ run IDs in company mode, avoiding cross-company upserts
  under a model-generated duplicate ID.
- The Objects browser runtime uses the authenticated user's JWT in company
  mode. The service-role key stays on the Streamlit server.
- The Auth session is restored after refresh from tab-scoped `sessionStorage`.
  The bridge runs in the hidden Sidebar so it cannot alter main-screen layout.
  Closing the tab clears this browser-held session.
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
   creation, a newly generated one-time employee link, rejection after its first
   successful use, member access removal, login, logout, direct deep links, and
   two-company data isolation.
5. Confirm anonymous REST requests can no longer read pricing overrides or
   object-estimate progress, and can no longer write pricing overrides.

## Known MVP limits

- Login persistence is tab-scoped. It survives refresh but intentionally does
  not survive closing the tab or opening the app in a different tab.
- Production login UI and invitation ergonomics need an end-to-end browser
  review. A leaked unused team invitation remains usable until its 24-hour
  expiry; explicit invitation revocation is intentionally outside this MVP.
- Membership revocation while a background Estimation job is already running
  does not cancel that job. The MVP removal UI revokes future company access but
  does not terminate a browser request already executing.
- The creator's Auth account cannot be deleted while its membership exists.
  An owner-transfer/recovery flow is needed before account deletion or
  self-service role management is introduced.
