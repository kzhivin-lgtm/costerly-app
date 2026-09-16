# Costerly UI guidelines

## Form interaction states

- Default fields use the shared neutral border.
- Focus is always a quiet Costerly-purple border and ring. Focus is never an
  error and must never be red.
- Do not show framework keyboard hints such as `Press Enter to submit form`.
- Empty required fields become invalid only after the user submits the form.
- A non-empty value that can be validated locally may become invalid on blur.
  Email is the canonical example.
- Any input event clears the visible invalid state so the interface does not
  continue scolding the user while they correct a value.
- Use a red border as the primary field-level validation signal. Do not repeat
  obvious instructions such as `Enter an email address` beneath a clearly
  labelled Email field.
- Show text only when it adds recovery information the field itself cannot
  communicate, for example an existing account or a temporary service failure.
- Validation must never erase input values or move the user away from the form.

## Visual consistency

- Use the shared light Costerly palette regardless of the browser or operating
  system theme until a complete dark theme is designed.
- Reuse shared input, button, spacing, focus, and error tokens before adding
  screen-specific CSS.
- Hover and active states should communicate interactivity without changing
  layout or moving surrounding content.
- Desktop and mobile versions use the same hierarchy, wording, and validation
  behavior; only dimensions and spacing may adapt.
