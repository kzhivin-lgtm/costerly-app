# Cold Upload bootstrap checkpoint, 3.18.1 and 3.18.3

Status: owner accepted in authenticated production on 2026-10-10.

## Protected result

- First authenticated Upload is not held by Platform Admin or Last Estimate
  reads. They prefetch after the first reveal without polling or a follow-up
  Streamlit rerun.
- Company membership remains an RLS gate before any authenticated content.
- Fast Resume remains a single Python run. Native controls, the transition mask,
  and the accepted Price Lists screen are unchanged.
- Sign in overlaps the independent Terms and membership checks only after the
  password grant is accepted. Both gates complete before Upload renders.

## Production evidence

The accepted cold Upload hard reload samples were 3.05 s, 3.06 s and 3.23 s,
median 3.06 s. The immediately preceding comparable median was 3.36 s.
Server critical-path median fell from 1.03 s to 0.28 s.

Fresh Sign in to Upload traces after the change measured 1.98 s, 2.46 s,
2.58 s and 2.98 s. These values remain network-sensitive and are not a reason
to weaken the mandatory RLS or legal gates.

## Deferred boundary

The remaining cold delay belongs predominantly to wrapper and iframe Streamlit
bootstrap plus the mandatory RLS request. Do not re-open this checkpoint for
micro-tweaks. Measure a new performance task first if further work is proposed.
