# Estimation 9.47 Profile reliability and Production overhead capacity

Status: candidate, 23 November 2026, existing work3.17.4.6. Owner authorised
continuing the cycle from the full9.46 checkpoint (runtimec731f2ac,
records6606568f). No Detection/Parts/material/catalog/provider/schema change.

## Contacts diagnosis and repair

[verified] The owner trace44f8a155 at13:32:20UTC completes company data in222.616ms
and logo load in852.319ms, then emits no content-complete/ready. After Reload,
trace03a3bc2b at13:32:49UTC reads those resources in0.049/0.335ms and again has
no completion. It is not evidence of a slow company query.

The unchanged9.46 UI reproduces StreamlitInvalidLayoutContextError when Contacts
has an existing logo: install_company_logo_picker_guard enters st.sidebar from
_render_profile_tabs, a fragment. That outside slot was not created during the
initial full render. The guard is now in a hidden, fragment-owned container.
Its existing native-picker event and cleanup remain. No ready check, timeout,
auth rule or cover was weakened. Previous Profile fixtures had no stored logo
and did not execute this conditional branch. New permanent cases cover stored
logo, repeated tab switches, desktop/narrow and Reload, plus Change Logo picker.

## Overhead allocation

[verified] The owner company has six active Production employees reporting a
sum1200 monthly hours. All1200 reported hours currently belong to Production.
Legacy settings remain12 workers*21 days*8 hours=2016. New calculation reads only
monthly_hours for the current company, Production department and nondeleted
rows. No wages/names are read and the reported count detects truncated results.
The same capacity settings feed both Object Detail and persisted full object
cost. Monthly overhead*current object production hours/capacity and existing
reserve/VAT formulas are otherwise unchanged. Production add/edit/delete
invalidates only that company's overhead/cost views, preserving saved Labor.

When no Production hours are reported, the existing configured legacy capacity
is retained as an explicit audited fallback, not an invented salary-hours policy.
Reported/unreported counts and capacity source are retained in the cost audit.
A failed capacity read is not silently converted to the fallback.

Read-only saved kitchen replay, with the current Profile settings and identical
Materials/Labor:21.8459166667h, denominator2016→1200, overhead1009.14→1133.69ILS.
This is not a new complete estimate and performed no write/provider call. It
must not be compared to the earlier173ILS screenshot without accounting for the
owner's changed3%+3% reserves. Markup50/buffer3/warranty3/installation15/
packaging1/delivery5 were confirmed saved and were not overwritten.

## Interface scope

With all three cost bands collapsed, remove only the automatic viewport filler
before Self Cost. It follows Overhead in natural flow; fixed Privacy remains.
This intentionally supersedes bottom-pinned summary/actions only in the fully
collapsed state. Expanded states retain the prior26px footer clearance. Short
collapsed pages may have unused viewport space below their content.

Profile save receipts now produce Saving…→Saved on the same action, with no green
bottom success alert. Saved appears only after the existing write succeeds,
resets after2s or immediately on a new edit. Failed writes retain their existing
errors/drafts and restore the Save action. Existing native/bridge write handlers
are reused, no new persistence request, price cycle or Profile rerun is added.
Deletes retain actual row removal and an invisible receipt, without a new notice.

One scoped client guard owns the current Profile Save. Its observer starts only
for a save and observes receipts/stale/tab changes until ack/error/navigation or
30s UI timeout; one2s presentation timer follows an acknowledged Saved. Both
cancel on edit/tab/dispose as appropriate. Company/action/fresh receipt IDs reject
stale acknowledgements. Input after submission does not receive a false Saved.
The zero-height bridge and logo guard create no visible layout slots.

## Verification and limits

- Negative stored-logo reproduction and corrected local repeated Contacts/picker
  passed; isolated1280/390 cases include Reload.
- Profile feedback pending/ack/reset/new-edit passed without another render.
-40 focused Overhead/cost/Profile tests passed, including add/edit/delete cache
  invalidation, current-company query scope and explicit fallback/read failure.
- Existing Calculation UI plus eight collapse combinations per width passed;
  Object Save/green Saved/Back/APPROVE lock and expanded26px clearance retained.
- Four frozen material controls match, network disabled, no source mutation or
  changed purchase signatures. No fresh recognition/model run was needed.
- An early repeated Profile fixture run was invalid because it reused already
  modified machinery data; it did not justify a product change. Isolated runs
  and the final full contract use separate state/processes.
- Full clean local/exact-SHA GitHub gates and actual deployed identities remain
  required. Synthetic acceptance is distinct from owner authenticated acceptance.

Evidence: outputs/estimation-v9.47 in the handoff workspace. The existing separate
Workers Builds failure remains deferred. Full UI-contract consolidation after
the owner's final UI acceptance remains a separate pending request; current
approved changes and all preceding protection are added to the contract now.
