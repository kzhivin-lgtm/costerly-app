# TODO

Working task log for Costerly. The top section is the current focus; backlog
keeps important follow-up work visible without mixing it into the active scope.

## Current

No active task. Next task starts as v1.9.0.

## Backlog

### Streamlit initial loading flicker
Priority: low

- Hide technical Streamlit loading flashes during first app load.
- Compare with the old app later; one flicker case was already solved there.

## Done

### v1.3.0 - Detected object card edit layout
- Reworked the detected object card with editable object name and QTY fields.
- Added CONF display and Ignore visual control.
- Aligned Dimensions, Materials, and Missing information with File Review card style.

### v1.2.0 - File Review screen
- Rebuilt the old File Review layout in the new screen structure.
- Used a dev-only visual fixture until the real detection use case is connected.
- Aligned the post-upload screen title origin with Processing.

### v1.0.1 - Upload dragover state
- Added dragover state for the custom upload box.
- On dragover: lilac fill/border and a large white plus.
- Avoided dynamic Streamlit/Emotion class names.

### v1.0.0 - Upload screen foundation
- Built the first upload screen: logo, hero, upload box, hover, responsive base.
- Added local brand and font assets.
- Hid Streamlit toolbar/deploy controls.

### v1.8.0 - Agent usage ledger
- Added agent_usage_events persistence for Detection Agent runs.
- Stored input/output token counts, prompt version, model, file name, and run ID.
- Added default Claude pricing catalog with optional secrets override for USD cost tracking.
