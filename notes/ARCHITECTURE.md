# Costerly Architecture

Costerly Streamlit should stay a thin UI shell.

```text
Streamlit UI
  screens / ui / styles
        ↓
Application use cases
        ↓
Services
        ↓
Supabase / Anthropic / file parsing
Rule
Screens receive user actions and render state. They do not own business logic.
Theme Policy
The design system has light and dark token blocks.
For now, both blocks intentionally produce the same light Costerly UI. This lets us add a real dark theme later by changing dark tokens without rewriting screens.
The app should not follow Streamlit native dark mode yet.
Responsive Policy
Every screen should be designed for desktop and mobile from the start.
For each screen, define:
desktop layout;
mobile layout;
what changes at max-width: 760px;
what must not shift or overlap.
RFQ Processing Target Flow
uploaded file accepted by Streamlit
        ↓
process_uploaded_rfq()
        ↓
parse file metadata/content
        ↓
run detection agent
        ↓
validate and normalize detection result
        ↓
persist RFQ run and detected objects
        ↓
render review screen
Comments
Code comments should explain responsibility and timing:
why a module exists;
when a function is called;
what the function deliberately does not do.
Avoid comments that repeat obvious code.
MD
```
