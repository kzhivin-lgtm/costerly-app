# Legal Consent and Verified Registration

Task: 3.11.1
Status: completed and accepted in production at `3a4d8fa`; post-checkpoint legal revision active at `bc198fb`

Final owner confirmation on 25.09.2026 closes the production signup,
email-confirmation, returning-user gate, mobile, Terms, and Privacy acceptance
scope. This supersedes the earlier pending-state notes retained below as task
history.

## Verified legal revision on 2026-09-26

- Terms 1.4 is publicly deployed and selected by the Supabase release pointer
  with material acceptance version 5. Its live response SHA-256 is
  `16092ef0d0373774dfb4023d2ed15bc866170bf56224a5d16cdf7cea10f494f5`.
- Privacy 1.3 is publicly deployed and selected independently with unchanged
  acceptance version 1 and `requires_reacceptance = false`. Its live response
  SHA-256 is
  `21f380232a37c56c8e0b6f5b735d2be556cb3e0ddf551360fb90c67bfb87b978`.
- The final Customer Content model has three layers. Authorized personnel may
  access identifiable Raw Customer Content, as reasonably necessary, only for
  service operation, support, QA, troubleshooting, security, error analysis,
  and testing, evaluation and improvement of Costerly AI workflows. Broad
  market-intelligence rights apply only to validly aggregated or de-identified
  Derived Data that cannot reasonably identify or reconstruct a Customer,
  User, third party, counterparty, project, source document, Customer Content,
  Output, personal data, Customer-specific confidential information or a
  confidential commercial relationship. Generalized know-how is retained on
  the same non-disclosure and non-reconstruction boundary.
- One existing Terms 1.3 acceptance event was present at activation. The
  server confirms that this user has acceptance history and now requires the
  current Terms 1.4 acceptance. No pending registration existed.
- The release preserves Customer ownership of Customer Content and Output,
  AI-provider no-training commitments, Section 15 indemnity, separate-DPA
  support, and applicable-law deletion and retention qualifications.
- This legal revision does not itself create a Derived Data product or
  processing pipeline. Any later implementation must enforce aggregation and
  de-identification controls sufficient to prevent reasonable identification
  or reconstruction; those controls must not rely on the contractual label
  alone.
- The full deterministic suite passes: 400 tests.

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
- At the prior Terms 1.3 checkpoint, the full deterministic suite passed: 343 tests.
- Material Terms of Service version 1.1 and Privacy Policy version 1.1 are
  active. Terms acceptance version advanced from 1 to 2; Privacy remains
  acceptance version 1 and does not create its own gate. There were no existing
  acceptance events or pending registrations when version 1.1 was activated.
- Material Terms of Service version 1.2 is publicly deployed and selected by
  the Supabase release pointer. Its live response SHA-256 is
  `aadc32bc8cf8c2b30d8d8d7b4e721ee5864fd39d6c61ca54ddee30e6b00a5ec3`,
  and it advances the acceptance version from 2 to 3. It makes the Customer the organization
  and contractual subscription holder; defines Admins and Members as Users;
  separates an authorized payer from the Customer; attributes User acts and
  omissions to the Customer; strengthens third-party indemnity, AI-provider
  no-training configuration, and billing language; identifies Costerly AI only
  as the Operator's trade name; and adds baseline controller, processor,
  subprocessor, security, breach, assistance, transfer, deletion and DPA terms.
  Privacy remained at version 1.1 when the Terms revision was activated. There
  were no acceptance events or pending registrations at that time.
- Privacy Policy version 1.2 is publicly deployed and selected by the Supabase
  release pointer as an independent, non-blocking release. Its live response
  SHA-256 is
  `baee97a79a3be012dec6b0e5610aa380abd01e753dd64930ea97ec25bf13d674`.
  It narrows Customer Content use, aligns the AI-provider commitment
  with Terms, explains that required account/contact data is voluntary under
  law but necessary to provide the account, describes the actual first-party
  resume storage and browser/server telemetry without inventing third-party
  analytics, strengthens international-transfer language, and uses the same
  Operator and trade-name wording as Terms. Privacy acceptance version remains
  1, `requires_reacceptance` is false, and the release does not trigger Terms
  reacceptance.
- Terms of Service version 1.3 is publicly deployed and selected by the
  Supabase release pointer as the final pre-launch text pass. Its live response
  SHA-256 is
  `346cb5ee4be1cac1b0fa4a80deb8c1a89a330e426dae8d931485b79233cc2b0d`.
  It makes each accepting User individually bound by User provisions, removes
  permission to use Customer Content to develop service functionality, and
  standardizes the Operator identifier as `registration no. 346904519`. The
  accepted indemnity, separate-DPA clause, and `Subject to applicable law`
  retention protection remain unchanged. This material release advances the
  Terms acceptance version from 3 to 4. There were no acceptance events or
  pending registrations when it was activated. The deterministic suite passes:
  343 tests.
- The frozen legal-text checkpoint is commit `ef31dca`. A validated local
  backup is stored at
  `backups/v3.11.1_legal_text_final_checkpoint/costerly-app_v3.11.1_legal_text_final_checkpoint_2026-09-25.zip`
  (738,601 bytes, SHA-256
  `412765eeead3737b3dad3fb8d682123042be869e9effb5bac4ad816d8b583958`).
  This checkpoint closes the legal-copy sub-scope only; the production signup,
  email-confirmation and returning-user acceptance matrix remains active.

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
