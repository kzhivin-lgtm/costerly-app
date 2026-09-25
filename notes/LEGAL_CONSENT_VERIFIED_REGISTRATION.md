# Legal Consent and Verified Registration

Task: 3.11.1
Status: version 1.1 activated, production acceptance incomplete

## Verified progress on 2026-09-25

- The additive production migration has been applied. A service-role read
  confirmed all five legal-consent tables exist.
- The operator supplied the Hebrew and English name and confirmed registration
  in Israel as an exempt dealer (`osek patur`) under business registration and
  exempt dealer number 346904519.
- Company-creation and member-invitation signup both require one unchecked
  Terms control on their only submit. Successful signup advances to email
  verification. Returning authenticated users are gated before application
  controls only when the current Terms acceptance version is missing.
- The owner authorized the current working copy to be published as playground
  version 1.0 before external user access. Later material text changes will use
  a new immutable document version and acceptance version.
- Public Terms and Privacy versions 1.0 remain as immutable history. Version
  1.1 is deployed and selected by both Supabase release pointers. The live
  response-byte SHA-256 values are
  `c57cb8acd7fc91a59d05a6c49bf0fc52b9efbf1e614500a092d59039952630c1`
  for Terms and
  `96fbec67a23be6b518a60ae42d988a8e86f745de1e2b718f8a32b03131b44801`
  for Privacy. Supabase Auth reports `mailer_autoconfirm=false`.
- Production anonymous verification through `https://app.costerly.ai/` confirms
  the company invitation shows one submit, collapsed Terms, an unchecked
  mandatory control, and Privacy links in both the form and wrapper footer.
  Normal Sign in does not reveal Terms before authentication. The verification
  invitation remains unused.
- A mailbox-backed signup, received confirmation message, confirmation click,
  company activation, existing-user gate, mobile pass, and branded Supabase
  Confirm Signup template remain acceptance work. This is active playground
  functionality, not a completed production checkpoint.
- The full deterministic suite passes: 335 tests.
- Material Terms of Service version 1.1 and Privacy Policy version 1.1 are
  active. Terms acceptance version advanced from 1 to 2; Privacy remains
  acceptance version 1 and does not create its own gate. There were no existing
  acceptance events or pending registrations when version 1.1 was activated.

This file is the scenario-first product contract for Terms of Service,
Privacy Policy visibility, email verification, and later material Terms
acceptance. It does not establish legal approval of the document text.

## Agreed product decisions

- The contractual document is named `Terms of Service`.
- Signup and the post-auth gate show the Terms title plus the real opening
  paragraph, fading through its third line. Activating that disclosure expands
  the complete Terms inline without an additional full-document link. Reading
  or expanding it is optional. The unchecked agreement control is mandatory.
- Privacy Policy is acknowledged by being clearly provided at signup and is
  always available from the public application footer. It has no checkbox.
- A valid signup advances to a minimal branded screen containing only
  `Check your email to verify your account`, plus a quiet support route when
  delivery does not arrive.
- Email is verified once. Later material Terms releases require only a new
  acceptance. Privacy-only releases do not block application access.
- Trial terms do not promise a fixed number of days. The applicable plan or
  offer defines the Trial Period.
- Company or membership activation happens only after email verification.
- Legal status is never looked up from an unauthenticated typed email. New
  registrations always show Terms. Returning users authenticate first; the
  server then checks acceptance by verified `user_id`, so accepted current
  Terms never appear during their normal application entry.

## Protected behavior

- Existing one-time company creation and member invitations remain the only
  registration entry points.
- Invitation tokens remain opaque, one-use, and server-validated.
- Existing Sign in, password recovery, tab-scoped session restoration, native
  Sign out, Auth geometry, and application navigation remain unchanged.
- Legal records are server-written and append-only. Browser state is not legal
  evidence and cannot create or alter an acceptance record.
- Activation requires the additive migration, published legal documents and
  Confirm Email behavior to agree. The private playground may use Supabase's
  default mail delivery while the branded template and production SMTP remain
  explicit pre-user-access work.

## Scenario matrix

| State or action | Expected behavior |
| --- | --- |
| Signup opens | Show the established company or member fields, the Terms disclosure with a three-line fading preview, and the unchecked agreement control |
| Anonymous visitor types an email | Do not reveal whether the address exists, is verified, or accepted a Terms release; do not dynamically hide legal controls |
| User opens or closes Terms | Expand the complete current Terms inline and preserve every field and checkbox value; opening and reading are optional |
| Privacy Policy link is used | Keep it in the permanent wrapper footer, open the current policy separately, and preserve signup state |
| Terms is unchecked | Do not create an Auth user, acceptance event, company, or membership; mark the agreement control |
| Multiple fields are invalid | One submit marks every invalid field including the agreement control; no loading state starts |
| User corrects an invalid value | Clear that field's invalid state without clearing unrelated fields |
| Valid signup is submitted | Resolve current published document versions and hashes on the server, create one unverified Auth user, append one signup acceptance, persist one pending registration, and show the verification screen |
| Submit is clicked repeatedly | Disable duplicate submission and create at most one Auth user, pending registration, and signup acceptance |
| Auth provider rejects or times out | End loading, preserve editable values, show an actionable service error, and permit a safe retry |
| Existing confirmed email is submitted | Do not reveal account existence; show the same verification result without creating another legal event or registration |
| Verification screen opens | Show the brand and `Check your email to verify your account`; do not expose application or company data |
| Message does not arrive | Offer a quiet `Contact support` route; do not claim delivery failure that the provider did not report |
| Verification screen is refreshed or revisited | Keep the account inactive; Sign in before verification returns to the verification state |
| Correct confirmation link is opened | Restore the verified session, atomically consume the saved invitation, create the company or membership, bind the signup acceptance to the company, and enter the application |
| Confirmation link is opened on another browser or device | Complete from the verified Supabase session without depending on the original Streamlit session |
| Confirmation link is expired, malformed, already used, or prefetched | Do not activate access; show an invalid-link state and a safe support route |
| Confirmation callback is repeated | Return the already completed company access without duplicating membership or legal records |
| User has accepted the current material Terms release | Enter the application normally |
| User has no acceptance | Before rendering company data, show `Terms of Service` with the shared disclosure and unchecked control |
| User accepted only an older material Terms release | Before rendering company data, show `Updated Terms of Service` with the shared disclosure and unchecked control |
| Terms gate is unchecked | Do not append an event or reveal application data |
| Current Terms is accepted | Append exactly one server event and continue immediately; do not reverify email |
| Terms acceptance is double-submitted or retried | Remain idempotent and append at most one event for the request |
| Terms acceptance write fails | Keep the gate, end loading, and allow retry without exposing application data |
| Privacy Policy alone changes | Update the permanent link and current version; do not show a blocking gate |
| Multiple tabs are open | Each tab rechecks server state; acceptance in one tab lets another continue on its next request |
| User signs out from the Terms gate | Clear the same browser and server session state as normal Sign out |
| Any public or authenticated screen is visible | Keep Privacy Policy available in the production wrapper footer |
| Keyboard, mobile, refresh, and back are used | Preserve the same outcomes and do not bypass the gate or duplicate writes |

## Acceptance evidence

Implementation requires deterministic coverage of every server outcome above.
Production acceptance must then execute this same matrix through
`https://app.costerly.ai/` in the owner's existing browser session, including a
real newly generated email. Source inspection, automated tests, a headless
screen, or one successful link is not final acceptance.

The legal drafts are implementation inputs only. Publishing v1 requires the
operator identity, notice addresses, governing law and venue, liability cap,
and retention/deletion language to receive an explicit legal-content review.

## Atomic rollout order

1. Approve final English Terms and Privacy content. Remove every draft marker.
2. Publish the two immutable Pages artifacts and compute SHA-256 over the exact
   released bytes.
3. Apply `db/sql/2026_09_25_legal_consent_verified_registration.sql`. Completed
   and verified on 2026-09-25.
4. Insert the two published document rows with their hashes, then point
   `legal_document_releases` to them. A material Terms release receives a new
   `acceptance_version`; an editorial release retains the prior one.
5. Configure production SMTP. Supabase's default sender is not a production
   delivery channel.
6. Paste `notes/email_templates/confirm_signup.html` and
   `confirm_signup.subject.txt` into the Supabase Confirm Signup template.
7. Keep Confirm Email enabled and allow exactly
   `https://app.costerly.ai/confirm` as the production confirmation redirect.
8. Deploy Railway and Cloudflare from the same source revision while the legal
   feature is still disabled.
9. Verify the public Terms, Privacy, logo, footer, callback route, email sender,
   and a newly generated Gmail iOS message.
10. Set `LEGAL_CONSENT_ENABLED=true`, deploy, then execute the complete matrix
    using fresh company and member invitations plus an existing accepted user.
11. Establish a checkpoint only after the database evidence, authenticated
    production behavior, desktop/mobile visuals, keyboard flow and protected
    Auth scenarios all pass.
