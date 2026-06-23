# TODO

Working task log for Costerly. The top section is the current focus; backlog
keeps important follow-up work visible without mixing it into the active scope.

## Current

### v1.0.1 - Upload dragover state
- Add dragover state for the custom upload box.
- On dragover: lilac fill/border and a large white plus.
- Do not depend on dynamic Streamlit/Emotion class names.

## Backlog

### Streamlit initial loading flicker
Priority: low

- Hide technical Streamlit loading flashes during first app load.
- Compare with the old app later; one flicker case was already solved there.

### Agent usage cost tracking
Priority: medium

- Add input tokens, output tokens, and total cost cents to agent output.
- Include usage metrics in the validated detection data contract.
- Store usage metrics in Supabase to track RFQ processing cost.

## Done

### v1.0.0 - Upload screen foundation
- Built the first upload screen: logo, hero, upload box, hover, responsive base.
- Added local brand and font assets.
- Hid Streamlit toolbar/deploy controls.
