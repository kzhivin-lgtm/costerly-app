from __future__ import annotations

import streamlit as st
import streamlit.components.v1 as components


_QUIET_FIELD_ERRORS = {
    "Enter an email address like name@company.com",
    "Enter your email to reset your password",
    "Enter your company name",
    "Password needs at least 8 characters, an uppercase letter, a lowercase letter and a number",
    "Passwords do not match",
    "Confirm your password",
}


def render_auth_field_error(
    field: str,
    message: str,
    *,
    show_message: bool = False,
) -> None:
    """Mark a field invalid and optionally show its actionable message."""
    st.markdown(
        f'<span class="auth-field-error-marker" data-auth-field="{field}"></span>',
        unsafe_allow_html=True,
    )
    if show_message:
        st.markdown(
            '<div class="auth-form-feedback auth-form-feedback-error '
            f'auth-form-feedback-dismissible" role="alert">{message}</div>',
            unsafe_allow_html=True,
        )
        return
    if message not in _QUIET_FIELD_ERRORS:
        st.error(message)


def install_auth_form_interactions() -> None:
    """Add quiet blur validation without turning the Streamlit form into custom HTML."""
    components.html(
        r"""
        <script>
        (() => {
          const doc = window.parent.document;
          const labels = {
            company: ["Your company name", "Company name"],
            email: ["Email"],
            password: ["Password", "New password"],
            confirm: ["Confirm Password", "Confirm password"]
          };

          function fieldShell(field, scope = doc) {
            const input = Array.from(scope.querySelectorAll('input')).find(
              (node) => labels[field]?.includes(node.getAttribute('aria-label'))
            );
            return input ? {input, shell: input.closest('[data-testid="stTextInput"]')} : null;
          }

          function validEmail(value) {
            const text = value.trim();
            const pieces = text.split('@');
            if (pieces.length !== 2) return false;
            const [local, domain] = pieces;
            if (!local || local.startsWith('.') || local.endsWith('.') || local.includes('..')) return false;
            if (/\s/.test(text)) return false;
            const labels = domain.split('.');
            if (labels.length < 2 || labels.some((label) => !label || label.startsWith('-') || label.endsWith('-'))) return false;
            const suffix = labels[labels.length - 1];
            return suffix.length >= 2 && !/^\d+$/.test(suffix);
          }

          function setInvalid(field, invalid, scope = doc) {
            const target = fieldShell(field, scope)?.shell;
            if (target) target.classList.toggle('costerly-auth-invalid', invalid);
          }

          function formHasAction(form, label) {
            return Array.from(
              form?.querySelectorAll('div[data-testid="stFormSubmitButton"] button') || []
            ).some((button) => (
              button.textContent.trim() === label ||
              button.dataset.costerlyOriginalLabel === label
            ));
          }

          function fieldIsValid(field, scope = doc) {
            const target = fieldShell(field, scope);
            if (!target) return true;
            const value = target.input.value;
            if (field === 'company') return value.trim().length > 0;
            if (field === 'email') return validEmail(value);
            if (field === 'password') {
              if (formHasAction(target.input.closest('div[data-testid="stForm"]'), 'Sign in')) {
                return value.length > 0;
              }
              return value.length >= 8 && /[a-z]/.test(value) && /[A-Z]/.test(value) && /[0-9]/.test(value);
            }
            if (field === 'confirm') {
              const password = fieldShell('password', scope)?.input.value || '';
              return value.length > 0 && value === password;
            }
            return true;
          }

          function termsControl(scope = doc) {
            return Array.from(scope.querySelectorAll('[data-testid="stCheckbox"]')).find(
              (node) => node.textContent.includes('I have read and agree to the Terms of Service')
            ) || null;
          }

          function termsIsValid(scope = doc) {
            const control = termsControl(scope);
            return !control || Boolean(control.querySelector('input:checked'));
          }

          function setTermsInvalid(invalid, scope = doc) {
            termsControl(scope)?.classList.toggle('costerly-auth-invalid', invalid);
          }

          function setLoadingLabel(button, text) {
            const label = button?.querySelector('p');
            if (label) label.textContent = text;
          }

          function endAuthOperation(form) {
            if (!form?.classList.contains('costerly-auth-loading')) return;
            form.classList.remove('costerly-auth-loading');
            form.removeAttribute('aria-busy');
            form.querySelectorAll('input').forEach((input) => {
              input.readOnly = false;
              input.removeAttribute('aria-disabled');
            });
            const button = form.querySelector(
              'div[data-testid="stFormSubmitButton"] button[data-costerly-original-label]'
            );
            if (button) {
              const sent = Boolean(form.querySelector('.auth-recovery-sent'));
              if (sent && button.dataset.costerlyOriginalLabel === 'Forgot password?') {
                const container = button.closest('div[data-testid="stFormSubmitButton"]');
                (container || button).style.display = 'none';
              } else {
                button.disabled = false;
                setLoadingLabel(
                  button,
                  button.dataset.costerlyOriginalLabel || button.textContent.trim()
                );
              }
              delete button.dataset.costerlyOriginalLabel;
            }
            form.querySelector('.costerly-auth-loading-message')?.remove();
          }

          function beginAuthOperation(button, loadingLabel) {
            const form = button.closest('div[data-testid="stForm"]');
            if (!form || form.classList.contains('costerly-auth-loading')) return;
            const originalLabel = button.textContent.trim();
            button.dataset.costerlyOriginalLabel = originalLabel;
            form.classList.add('costerly-auth-loading');
            form.setAttribute('aria-busy', 'true');
            form.querySelectorAll('input').forEach((input) => {
              input.readOnly = true;
              input.setAttribute('aria-disabled', 'true');
            });
            button.disabled = true;
            setLoadingLabel(button, loadingLabel);
            if ([
              'Sign in',
              'Create account',
              'Forgot password?',
              'Reset password'
            ].includes(originalLabel)) {
              const oldShell = doc.getElementById('costerly-auth-sign-in-shell');
              if (oldShell) oldShell.remove();
              const app = doc.querySelector('.stApp');
              if (app) {
                const shell = app.cloneNode(true);
                shell.id = 'costerly-auth-sign-in-shell';
                shell.setAttribute('aria-hidden', 'true');
                Object.assign(shell.style, {
                  position: 'fixed',
                  inset: '0',
                  zIndex: '2147483200',
                  width: '100vw',
                  height: '100vh',
                  overflow: 'hidden',
                  pointerEvents: 'none',
                  background: '#F1EFEF',
                });
                doc.body.appendChild(shell);
                window.setTimeout(() => shell.remove(), 15000);
              }
            }
          }

          function dismissOperationError(input) {
            const form = input.closest('div[data-testid="stForm"]');
            form?.querySelectorAll('[data-testid="stAlert"]').forEach((alert) => {
              const container = alert.closest('[data-testid="stElementContainer"]');
              (container || alert).style.display = 'none';
            });
            form?.querySelectorAll('.auth-form-feedback-dismissible').forEach((feedback) => {
              const container = feedback.closest('[data-testid="stElementContainer"]');
              if (container) {
                container.dataset.costerlyDismissedFeedbackId = feedback.dataset.authFeedbackId || '';
              }
              (container || feedback).style.display = 'none';
            });
          }

          function bindCompanyCreation() {
            const button = Array.from(
              doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
            ).find((node) => node.textContent.trim() === 'Create Company Account');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              const form = button.closest('div[data-testid="stForm"]');
              const fields = ['company', 'email', 'password', 'confirm'];
              const invalid = fields.filter((field) => !fieldIsValid(field, form));
              invalid.forEach((field) => setInvalid(field, true, form));
              setTermsInvalid(!termsIsValid(form), form);
              if (invalid.length > 0 || !termsIsValid(form)) return;
              window.setTimeout(() => beginAuthOperation(button, 'Checking your details...'), 0);
            });
          }

          function bindSignIn() {
            const button = Array.from(
              doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
            ).find((node) => node.textContent.trim() === 'Sign in');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              const form = button.closest('div[data-testid="stForm"]');
              const invalid = ['email', 'password'].filter((field) => {
                return !fieldIsValid(field, form);
              });
              ['email', 'password'].forEach(
                (field) => setInvalid(field, invalid.includes(field), form)
              );
              if (invalid.length > 0) return;
              window.setTimeout(() => beginAuthOperation(button, 'Signing in...'), 0);
            });
          }

          function bindMemberCreation() {
            const button = Array.from(
              doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
            ).find((node) => node.textContent.trim() === 'Create account');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              const form = button.closest('div[data-testid="stForm"]');
              const invalid = ['email', 'password', 'confirm'].filter(
                (field) => !fieldIsValid(field, form)
              );
              invalid.forEach((field) => setInvalid(field, true, form));
              setTermsInvalid(!termsIsValid(form), form);
              if (invalid.length > 0 || !termsIsValid(form)) return;
              window.setTimeout(() => beginAuthOperation(button, 'Creating account...'), 0);
            });
          }

          function bindTermsAcceptance() {
            const form = Array.from(doc.querySelectorAll('div[data-testid="stForm"]')).find(
              (node) => termsControl(node) && Array.from(
                node.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
              ).some((button) => button.textContent.trim() === 'Continue')
            );
            const button = Array.from(
              form?.querySelectorAll('div[data-testid="stFormSubmitButton"] button') || []
            ).find((node) => node.textContent.trim() === 'Continue');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              setTermsInvalid(!termsIsValid(form), form);
              if (!termsIsValid(form)) return;
              window.setTimeout(() => beginAuthOperation(button, 'Continuing...'), 0);
            });
          }

          function bindPasswordRecoveryRequest() {
            const button = Array.from(
              doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
            ).find((node) => node.textContent.trim() === 'Forgot password?');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.classList.add('costerly-forgot-password-button');
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              const form = button.closest('div[data-testid="stForm"]');
              if (!fieldIsValid('email', form)) {
                setInvalid('email', true, form);
                return;
              }
              window.setTimeout(() => beginAuthOperation(button, 'Sending reset link...'), 0);
            });
          }

          function bindPasswordUpdate() {
            const button = Array.from(
              doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
            ).find((node) => node.textContent.trim() === 'Reset password');
            if (!button || button.dataset.costerlyLoadingBound === '1') return;
            button.dataset.costerlyLoadingBound = '1';
            button.addEventListener('click', () => {
              const form = button.closest('div[data-testid="stForm"]');
              if (!fieldIsValid('password', form)) {
                setInvalid('password', true, form);
                setInvalid('confirm', false, form);
                return;
              }
              setInvalid('password', false, form);
              if (!fieldIsValid('confirm', form)) {
                setInvalid('confirm', true, form);
                return;
              }
              setInvalid('confirm', false, form);
              window.setTimeout(() => beginAuthOperation(button, 'Resetting password...'), 0);
            });
          }

          function refresh() {
            doc.querySelectorAll('.auth-form-feedback').forEach((feedback) => {
              const container = feedback.closest('[data-testid="stElementContainer"]');
              if (!container) return;
              const feedbackId = feedback.dataset.authFeedbackId || '';
              if (container.dataset.costerlyDismissedFeedbackId !== feedbackId) {
                container.style.removeProperty('display');
              }
            });
            doc.querySelectorAll('div[data-testid="stForm"].costerly-auth-loading').forEach((form) => {
              if (form.querySelector('.auth-field-error-marker, .auth-recovery-sent, .auth-form-feedback, [data-testid="stAlert"]')) {
                endAuthOperation(form);
              }
            });
            doc.querySelectorAll('div[data-testid="stForm"]').forEach((form) => {
              const invalidFields = new Set(
                Array.from(form.querySelectorAll('.auth-field-error-marker')).map(
                  (marker) => marker.dataset.authField
                )
              );
              Object.keys(labels).forEach((field) => {
                if (fieldShell(field, form)) {
                  setInvalid(field, invalidFields.has(field), form);
                }
              });
            });
            Object.keys(labels).forEach((field) => {
              const target = fieldShell(field);
              if (!target || target.input.dataset.costerlyAuthBound === '1') return;
              target.input.dataset.costerlyAuthBound = '1';
              target.input.addEventListener('focus', () => dismissOperationError(target.input));
              target.input.addEventListener('input', () => {
                const form = target.input.closest('div[data-testid="stForm"]');
                dismissOperationError(target.input);
                if (target.shell.classList.contains('costerly-auth-invalid')) {
                  setInvalid(field, !fieldIsValid(field, form), form);
                }
                if (field === 'password') {
                  const confirm = fieldShell('confirm', form);
                  if (confirm?.shell.classList.contains('costerly-auth-invalid')) {
                    setInvalid('confirm', !fieldIsValid('confirm', form), form);
                  }
                }
              });
              if (field === 'email') {
                target.input.addEventListener('blur', () => {
                  const value = target.input.value.trim();
                  setInvalid('email', value.length > 0 && !validEmail(value));
                });
              }
            });
            doc.querySelectorAll('[data-testid="stCheckbox"]').forEach((control) => {
              if (!control.textContent.includes('I have read and agree to the Terms of Service')) return;
              const input = control.querySelector('input');
              if (!input || input.dataset.costerlyTermsBound === '1') return;
              input.dataset.costerlyTermsBound = '1';
              input.addEventListener('change', () => setTermsInvalid(!input.checked, control.closest('div[data-testid="stForm"]') || doc));
            });
            bindCompanyCreation();
            bindSignIn();
            bindMemberCreation();
            bindPasswordRecoveryRequest();
            bindPasswordUpdate();
            bindTermsAcceptance();
          }

          refresh();
          const observer = new MutationObserver(refresh);
          observer.observe(doc.body, {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['data-auth-feedback-id']
          });
          window.addEventListener('beforeunload', () => observer.disconnect(), {once: true});
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def show_company_creation_started() -> None:
    """Advance the client label only after the account check succeeded."""
    components.html(
        r"""
        <script>
        (() => {
          const doc = window.parent.document;
          const button = Array.from(
            doc.querySelectorAll('div[data-testid="stFormSubmitButton"] button')
          ).find((node) => node.dataset.costerlyOriginalLabel === 'Create Company Account');
          const label = button?.querySelector('p');
          if (label) label.textContent = 'Creating your company...';
        })();
        </script>
        """,
        height=0,
        width=0,
    )


def apply_auth_css() -> None:
    """Keep account forms readable regardless of Streamlit's browser theme."""
    st.markdown(
        r"""
        <style>
        .stApp:has(.auth-screen-active),
        .stApp:has(.auth-screen-active) [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
            background: var(--color-bg) !important;
            color: #2A1F2C !important;
        }

        /* Keep the v3.0.43 logo coordinates, but let the shared page scroll it. */
        .stApp:has(.auth-screen-active) .costerly-app-header {
            position: absolute;
            top: calc(var(--app-header-top) - var(--app-content-top) - 16px);
        }

        .stApp:has(.auth-screen-active) .block-container,
        .stApp:has(.auth-screen-active) [data-testid="stMainBlockContainer"] {
            width: min(var(--primary-panel-width), calc(100vw - 32px)) !important;
            max-width: var(--primary-panel-width) !important;
            box-sizing: border-box !important;
            margin: 0 auto !important;
            padding: var(--app-content-top) 0 72px !important;
            background: transparent !important;
        }

        .auth-brand {
            margin-top: -31px;
            margin-bottom: 10px;
            text-align: center;
        }

        .auth-brand h1 {
            margin: 0;
            color: #2A1F2C;
            font-family: var(--font-brand);
            font-size: clamp(30px, 5vw, 35px);
            font-weight: 700;
            line-height: 1.1;
            letter-spacing: -0.045em;
        }

        .stApp:has(.auth-screen-active) .auth-brand a,
        .stApp:has(.auth-screen-active) .auth-brand [data-testid="stHeaderActionElements"],
        .stApp:has(.auth-screen-active) .auth-brand [data-testid="stHeadingWithActionElements"] > a {
            display: none !important;
        }

        .auth-brand p {
            margin: 0;
            color: #67616C;
            font-family: var(--font-sans);
            font-size: 16px;
            line-height: 1.5;
        }

        .auth-brand-sign-in,
        .auth-brand-join-your-company,
        .auth-brand-reset-password,
        .auth-brand-create-new-password {
            margin-bottom: 24px;
        }

        .auth-brand-sign-in h1,
        .auth-brand-join-your-company h1,
        .auth-brand-reset-password h1,
        .auth-brand-create-new-password h1,
        .auth-brand-terms-of-service h1,
        .auth-brand-updated-terms-of-service h1 {
            color: var(--color-purple, var(--primitive-purple-900));
            font-family: var(--font-hero);
            font-size: 46px;
            font-weight: 400;
            font-synthesis: none;
            letter-spacing: -0.045em;
            line-height: 1.18;
            -webkit-font-smoothing: antialiased;
            text-rendering: geometricPrecision;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] {
            background: #FFFFFF !important;
            border: 1px solid #E7DFE9 !important;
            border-radius: 20px !important;
            box-shadow: 0 18px 48px rgba(59, 46, 72, 0.08) !important;
            padding: 30px !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] label,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stWidgetLabel"] p {
            color: #2A1F2C !important;
            font-size: 14px !important;
            font-weight: 700 !important;
            line-height: 1.35 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] {
            background: #FFFFFF !important;
            border: 1px solid #CEC5D1 !important;
            border-radius: 10px !important;
            box-shadow: none !important;
            height: 52px !important;
            display: flex !important;
            align-items: center !important;
            overflow: hidden !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="InputInstructions"],
        .stApp:has(.auth-screen-active) [data-testid="stInputInstructions"],
        .stApp:has(.auth-screen-active) [class*="InputInstructions"] {
            display: none !important;
        }

        .stApp:has(.auth-screen-active) .auth-field-error-marker {
            display: none !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stElementContainer"]:has(.auth-field-error-marker) {
            display: none !important;
            height: 0 !important;
            min-height: 0 !important;
            margin: 0 !important;
            padding: 0 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInputRootElement"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="base-input"] {
            border-color: #CEC5D1 !important;
            box-shadow: none !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > div[data-baseweb="base-input"] {
            width: 100% !important;
            border: 0 !important;
            outline: 0 !important;
            box-shadow: none !important;
            background: transparent !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > div,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > button {
            height: 100% !important;
            display: flex !important;
            align-items: center !important;
            background: #FFFFFF !important;
            color: #51475B !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"]:focus-within [data-testid="stTextInputRootElement"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"]:focus-within div[data-baseweb="input"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"]:focus-within div[data-baseweb="base-input"] {
            border-color: #8049C6 !important;
            box-shadow: 0 0 0 3px rgba(128, 73, 198, 0.14) !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"].costerly-auth-invalid:not(:focus-within) [data-testid="stTextInputRootElement"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"].costerly-auth-invalid:not(:focus-within) div[data-baseweb="input"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stTextInput"].costerly-auth-invalid:not(:focus-within) div[data-baseweb="base-input"] {
            border-color: #B43E49 !important;
            box-shadow: 0 0 0 1px rgba(180, 62, 73, 0.10) !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input {
            height: 50px !important;
            min-height: 50px !important;
            box-sizing: border-box !important;
            padding: 0 16px !important;
            line-height: normal !important;
            background: #FFFFFF !important;
            color: #17191C !important;
            -webkit-text-fill-color: #17191C !important;
            caret-color: #8049C6 !important;
            font-size: 16px !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input::placeholder {
            color: #817A85 !important;
            -webkit-text-fill-color: #817A85 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input:-webkit-autofill,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input:-webkit-autofill:hover,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input:-webkit-autofill:focus,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] input:-webkit-autofill:active {
            -webkit-box-shadow: 0 0 0 1000px #FFFFFF inset !important;
            box-shadow: 0 0 0 1000px #FFFFFF inset !important;
            -webkit-text-fill-color: #17191C !important;
            caret-color: #8049C6 !important;
            transition: background-color 9999s ease-in-out 0s !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > div:last-child,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] button {
            background: transparent !important;
            border: 0 !important;
            border-left: 0 !important;
            border-radius: 0 !important;
            box-shadow: none !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > div:last-child::before,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] > div:last-child::after {
            display: none !important;
            border: 0 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] button,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] svg {
            background: transparent !important;
            color: #51475B !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] div[data-baseweb="input"] button svg path {
            fill: none !important;
            stroke: #51475B !important;
            stroke-width: 1.7px !important;
            stroke-linecap: round !important;
            stroke-linejoin: round !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"] [data-testid="stCaptionContainer"] p,
        .stApp:has(.auth-screen-active) div[data-testid="stForm"] small {
            color: #67616C !important;
            font-size: 13px !important;
            line-height: 1.45 !important;
        }

        .stApp:has(.auth-screen-active) .auth-password-row-marker {
            display: block;
            color: #2A1F2C;
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 700;
            line-height: 1.35;
        }

        .stApp:has(.auth-screen-active) .auth-recovery-sent {
            display: none !important;
        }

        .stApp:has(.auth-screen-active) .auth-verification-support {
            color: #67616C;
            font-family: var(--font-sans);
            font-size: 13px;
            line-height: 1.45;
            text-align: center;
        }

        .stApp:has(.auth-screen-active) .auth-verification-support a {
            color: #6F3CB4;
            font-weight: 600;
        }

        .stApp:has(.auth-screen-active) [data-testid="stCheckbox"].costerly-auth-invalid label > span:first-child {
            border-color: #B43E49 !important;
            box-shadow: 0 0 0 1px rgba(180, 62, 73, 0.10) !important;
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure {
            margin: 0 0 16px;
            color: #2A1F2C;
            font-family: var(--font-sans);
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure details {
            overflow: hidden;
            background: #FAF8FC;
            border: 1px solid #D8D0DC;
            border-radius: 10px;
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure summary {
            display: block;
            padding: 16px 18px 17px;
            cursor: pointer;
            list-style: none;
            user-select: none;
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure summary::-webkit-details-marker {
            display: none;
        }

        .stApp:has(.auth-screen-active) .auth-terms-title {
            display: flex;
            align-items: center;
            gap: 12px;
            color: #2A1F2C;
            font-size: 15px;
            font-weight: 600;
            line-height: 1.35;
        }

        .stApp:has(.auth-screen-active) .auth-terms-chevron {
            width: 8px;
            height: 8px;
            flex: 0 0 8px;
            border-right: 1.8px solid #51475B;
            border-bottom: 1.8px solid #51475B;
            transform: rotate(-45deg);
            transition: transform 150ms ease;
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure details[open] .auth-terms-chevron {
            transform: rotate(45deg) translate(-2px, -2px);
        }

        .stApp:has(.auth-screen-active) .auth-terms-preview {
            display: -webkit-box;
            max-height: 4.35em;
            margin: 11px 0 0 20px;
            overflow: hidden;
            color: #67616C;
            font-size: 14px;
            font-weight: 400;
            line-height: 1.45;
            -webkit-box-orient: vertical;
            -webkit-line-clamp: 3;
            mask-image: linear-gradient(to bottom, #000 42%, rgba(0, 0, 0, 0.72) 68%, transparent 100%);
            -webkit-mask-image: linear-gradient(to bottom, #000 42%, rgba(0, 0, 0, 0.72) 68%, transparent 100%);
        }

        .stApp:has(.auth-screen-active) .auth-terms-disclosure details[open] .auth-terms-preview {
            display: none;
        }

        .stApp:has(.auth-screen-active) .auth-terms-full {
            padding: 4px 20px 22px;
            border-top: 1px solid #E7DFE9;
            color: #51475B;
            user-select: text;
        }

        .stApp:has(.auth-screen-active) .auth-terms-full h2 {
            margin: 24px 0 8px;
            color: #2A1F2C;
            font-family: var(--font-sans);
            font-size: 16px;
            font-weight: 600;
            line-height: 1.35;
        }

        .stApp:has(.auth-screen-active) .auth-terms-full p,
        .stApp:has(.auth-screen-active) .auth-terms-full li {
            margin: 0 0 12px;
            color: #51475B;
            font-family: var(--font-sans);
            font-size: 14px;
            font-weight: 400;
            line-height: 1.55;
        }

        .stApp:has(.auth-screen-active) .auth-terms-full a {
            color: #6F3CB4;
            font-weight: 600;
        }

        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) {
            align-items: center !important;
            column-gap: 12px !important;
            margin-top: 2px !important;
            margin-bottom: -9px !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) [data-testid="stColumn"] {
            min-width: 0 !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) > [data-testid="stColumn"]:first-child {
            flex: 1 1 auto !important;
            width: auto !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) > [data-testid="stColumn"]:last-child {
            flex: 0 0 auto !important;
            width: auto !important;
        }

        .stApp:has(.auth-screen-active) .auth-form-feedback {
            margin-top: -3px;
            margin-bottom: 1px;
            display: block;
            font-family: var(--font-sans);
            font-size: 13px;
            font-weight: 600;
            line-height: 1.4;
        }

        .stApp:has(.auth-screen-active) .auth-form-feedback-error {
            color: #B43E49;
        }

        .stApp:has(.auth-screen-active) .auth-form-feedback-notice {
            color: #51475B;
        }

        .stApp:has(.auth-screen-active) .auth-form-feedback-success {
            color: #2F7D5A;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"],
        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] > div,
        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button {
            width: 100% !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button {
            min-height: 62px !important;
            margin-top: 10px !important;
            background: #8049C6 !important;
            border: 1px solid #8049C6 !important;
            border-radius: 11px !important;
            color: #FFFFFF !important;
            font-family: var(--font-sans) !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            text-transform: none !important;
            transition: background 150ms ease, border-color 150ms ease, transform 150ms ease, box-shadow 150ms ease !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button p {
            margin: 0 !important;
            color: #FFFFFF !important;
            font-family: var(--font-sans) !important;
            font-size: 20px !important;
            font-weight: 700 !important;
            line-height: 1.2 !important;
            letter-spacing: -0.01em !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"] {
            min-height: 30px !important;
            width: auto !important;
            margin-top: 0 !important;
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            color: #6F3CB4 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
            justify-content: flex-start !important;
            padding: 0 !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) div[data-testid="stFormSubmitButton"],
        .stApp:has(.auth-screen-active) [data-testid="stHorizontalBlock"]:has(.auth-password-row-marker) div[data-testid="stFormSubmitButton"] > div {
            width: auto !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"] p {
            color: #6F3CB4 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"]:hover {
            background: transparent !important;
            border: 0 !important;
            box-shadow: none !important;
            color: #5E2EA5 !important;
            transform: none !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stAlert"] {
            border: 0 !important;
            border-radius: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
            margin: 8px 0 0 !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stAlert"] > div {
            border: 0 !important;
            background: transparent !important;
            box-shadow: none !important;
            padding: 0 !important;
        }

        .stApp:has(.auth-screen-active) [data-testid="stAlert"] p {
            font-family: var(--font-sans) !important;
            font-size: 14px !important;
            line-height: 1.4 !important;
            font-weight: 600 !important;
            color: #B43E49 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button:hover {
            background: #6F3CB4 !important;
            border-color: #6F3CB4 !important;
            color: #FFFFFF !important;
            box-shadow: 0 8px 18px rgba(111, 60, 180, 0.20) !important;
            transform: translateY(-1px);
        }

        .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button:active {
            transform: translateY(0);
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading [data-testid="stTextInput"],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading [data-testid="stCaptionContainer"] {
            opacity: 0.48 !important;
            pointer-events: none !important;
            transition: opacity 160ms ease !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[data-costerly-original-label],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[data-costerly-original-label]:hover {
            position: relative !important;
            background: #7441B9 !important;
            border-color: #7441B9 !important;
            box-shadow: none !important;
            cursor: wait !important;
            transform: none !important;
            opacity: 1 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 10px !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[data-costerly-original-label] p {
            width: auto !important;
            flex: 0 0 auto !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
            gap: 10px !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[data-costerly-original-label] p::before {
            content: "";
            width: 17px;
            height: 17px;
            flex: 0 0 17px;
            border: 2px solid rgba(255, 255, 255, 0.42);
            border-top-color: #FFFFFF;
            border-radius: 50%;
            animation: costerly-auth-spin 700ms linear infinite;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"][data-costerly-original-label],
        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"][data-costerly-original-label]:hover {
            min-height: 30px !important;
            background: transparent !important;
            border: 0 !important;
            color: #6F3CB4 !important;
            box-shadow: none !important;
            justify-content: flex-start !important;
            padding-left: 16px !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"][data-costerly-original-label] p {
            color: #6F3CB4 !important;
            font-size: 14px !important;
            font-weight: 600 !important;
        }

        .stApp:has(.auth-screen-active) div[data-testid="stForm"].costerly-auth-loading div[data-testid="stFormSubmitButton"] button[kind="secondaryFormSubmit"][data-costerly-original-label] p::before {
            width: 14px;
            height: 14px;
            flex-basis: 14px;
            border-color: rgba(111, 60, 180, 0.28);
            border-top-color: #6F3CB4;
        }

        @keyframes costerly-auth-spin {
            to { transform: rotate(360deg); }
        }

        @media (max-width: 600px) {
            .stApp:has(.auth-screen-active) .block-container,
            .stApp:has(.auth-screen-active) [data-testid="stMainBlockContainer"] {
                width: calc(100vw - 24px) !important;
                max-width: none !important;
                padding-top: var(--app-content-top) !important;
                padding-bottom: 32px !important;
            }
            .stApp:has(.auth-screen-active) div[data-testid="stForm"] {
                padding: 20px !important;
            }
            .auth-brand h1 { font-size: clamp(27px, 8vw, 34px); }
            .auth-brand { margin-top: -17px; }
            .auth-brand-sign-in,
            .auth-brand-join-your-company,
            .auth-brand-reset-password,
            .auth-brand-create-new-password { margin-bottom: 24px; }
            .auth-brand-sign-in h1,
            .auth-brand-join-your-company h1,
            .auth-brand-reset-password h1,
            .auth-brand-create-new-password h1,
            .auth-brand-terms-of-service h1,
            .auth-brand-updated-terms-of-service h1 {
                font-size: clamp(30px, 9vw, 40px);
                line-height: 1.12;
            }
            .stApp:has(.auth-screen-active) .auth-terms-disclosure summary {
                padding: 15px 16px 16px;
            }
            .stApp:has(.auth-screen-active) .auth-terms-preview {
                margin-left: 20px;
            }
            .stApp:has(.auth-screen-active) .auth-terms-full {
                padding: 4px 16px 20px;
            }
            .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button {
                min-height: 58px !important;
                font-size: 18px !important;
            }
            .stApp:has(.auth-screen-active) div[data-testid="stFormSubmitButton"] button p {
                font-size: 18px !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
