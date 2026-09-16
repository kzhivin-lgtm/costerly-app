# Costerly UI guidelines

These rules apply to every Costerly screen and workflow. A missing interaction
state is a product defect, not optional polish.

## Product-wide interaction contract

- Every user action has four possible states: press, progress, completion, and
  error. Implement every state that the action can reach.
- A control must acknowledge pointer-down immediately. Hover alone is not
  feedback. Buttons need distinct default, hover, active, focus-visible,
  disabled, and loading states.
- Immediate press feedback must not wait for a server response or a Streamlit
  rerun. Use a small color, shadow, or scale response that does not move the
  surrounding layout.
- Any action expected to take longer than 500 ms must show a specific loading
  state immediately. Disable duplicate submission while preserving the user's
  entered data and current context.
- Loading labels must describe the current phase truthfully, for example
  `Checking file`, `Detecting objects`, or `Saving profile`. Do not say
  `Creating` while the system is still validating.
- Completion must be visible. Show the resulting state, navigate to the result,
  or display a concise success acknowledgement. Never leave a finished action
  looking as if it is still running.
- Failure must restore control immediately, preserve recoverable input, identify
  what failed, and state what the user can do next. Never leave a spinner or a
  disabled control behind after an error.
- Multi-stage progress must reflect measured work rather than equal fictional
  steps. Do not race to a high percentage and then stall near completion.
- Async work must be idempotent from the user's perspective. A double click,
  refresh, or retry must not create duplicate companies, RFQs, estimates, or
  writes.

## Form interaction states

- Default fields use the shared neutral border.
- Focus is always a quiet Costerly-purple border and ring. Focus is never an
  error and must never be red.
- Do not show framework keyboard hints such as `Press Enter to submit form`.
- Empty required fields become invalid only after the user submits the form.
- A non-empty value that can be validated locally may become invalid on blur.
  Email is the canonical example.
- After validation, an invalid state remains only while its condition is still
  unmet and clears immediately when the current value becomes valid.
- One submit validates every field. Do not stop at the first invalid value.
- Hidden validation markers must not reserve layout space or shift later fields.
- Use a red border as the primary field-level validation signal. Do not repeat
  obvious instructions such as `Enter an email address` beneath a clearly
  labelled Email field.
- Show text only when it adds recovery information the field itself cannot
  communicate, for example an existing account or a temporary service failure.
- Validation must never erase input values or move the user away from the form.
- Do not enter a loading state when local validation fails. Keep the user on the
  editable form and mark every invalid field instead.
- Use a truthful progress label. A server-side uniqueness check is `Checking`,
  not `Creating`; advance to creation only after that check succeeds. Any server
  validation error must immediately restore the editable form.

## Hierarchy and content

- Show the common path first. Put optional, advanced, or international settings
  one level deeper without hiding the primary task.
- Every element must earn its space. Remove redundant subtitles, repeated
  section names, framework instructions, and explanatory text that merely
  restates a clear label.
- Use direct, specific labels that describe the content or action. Prefer
  `Price Lists`, `Project Contact`, and `Save Details` over vague labels such as
  `Home`, `Settings`, or `Submit`.
- Group controls by the thing they affect. Proximity must communicate the same
  relationship as the data model.
- Every screen must make four things clear: where the user is, what is available,
  what the primary next action is, and how to leave or go back.
- Simplicity is not the same as removing context. Add short recovery or status
  text when it reduces uncertainty, but do not decorate obvious interactions.

## Motion and transitions

- Motion must explain state, location, causality, or progress. Do not animate an
  element only to make the interface look active.
- Frequently repeated actions should have little or no animation. Reserve more
  noticeable motion for occasional transitions where it improves orientation.
- Entering elements start promptly and settle with ease-out. Movement already
  on screen may use ease-in-out. Continuous progress indicators use linear
  motion. Avoid ease-in for interaction feedback because it delays the visible
  response.
- Prefer short transitions on `transform` and `opacity`. Do not animate layout
  properties when the same result can be achieved without reflow.
- User-controlled motion must remain interruptible and continue from its current
  visible position. Never force the user to wait for an animation to finish.
- Respect `prefers-reduced-motion`. Replace large movement, bounce, and parallax
  with a short fade or an immediate state change while preserving feedback.

## Accessibility and input methods

- Do not rely on color alone for important status. Pair it with shape, icon,
  label, or recovery text when the meaning would otherwise be ambiguous.
- Keyboard focus must remain visible and follow the same logical order as the
  page. Pointer-only and hover-only actions are not acceptable.
- Touch targets must be comfortably selectable on mobile. Do not shrink primary
  actions to fit a desktop layout.
- Text resizing must not clip labels, overlap controls, or hide actions. Use
  responsive sizing and spacing rather than assuming one fixed viewport.
- Loading and validation changes must be exposed as status to assistive
  technology without stealing focus unnecessarily.

## Visual consistency

- Use the shared light Costerly palette regardless of the browser or operating
  system theme until a complete dark theme is designed.
- Reuse shared input, button, spacing, focus, and error tokens before adding
  screen-specific CSS.
- Hover and active states should communicate interactivity without changing
  layout or moving surrounding content.
- Desktop and mobile versions use the same hierarchy, wording, and validation
  behavior; only dimensions and spacing may adapt.

## Review checklist

Before accepting a screen, verify:

1. Every clickable control responds on press, not only on hover.
2. Every network or agent action shows immediate and truthful progress.
3. Success, failure, retry, disabled, empty, and loading states all recover
   cleanly without layout jumps or lost data.
4. The primary action and current location are obvious without explanatory copy.
5. The screen works with keyboard, touch, narrow width, and reduced motion.
6. Repeated clicks and retries cannot duplicate persistent work.

## Design references

- Apple interface and motion principles distilled for the web:
  https://github.com/emilkowalski/skills/tree/main/skills/apple-design
- Emil Kowalski's broader design-engineering review principles:
  https://github.com/emilkowalski/skills/tree/main/skills/emil-design-eng

These references inform the rules above. They are not copied wholesale: Costerly
uses only the parts that improve clarity, responsiveness, accessibility, and
workflow reliability for its own product.
