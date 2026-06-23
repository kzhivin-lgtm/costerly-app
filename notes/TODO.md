# TODO

Working task log for Costerly. The top section is the current focus; backlog
keeps important follow-up work visible without mixing it into the active scope.

## Current

### v1.2.0 - File Review screen
- Rebuild the old File Review layout in the new screen structure.
- Use a dev-only visual fixture until the real detection use case is connected.
- Remove the temporary Processing -> File Review handoff when RFQ processing is wired.

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

### v1.0.1 - Upload dragover state
- Added dragover state for the custom upload box.
- On dragover: lilac fill/border and a large white plus.
- Avoided dynamic Streamlit/Emotion class names.

### v1.0.0 - Upload screen foundation
- Built the first upload screen: logo, hero, upload box, hover, responsive base.
- Added local brand and font assets.
- Hid Streamlit toolbar/deploy controls.
