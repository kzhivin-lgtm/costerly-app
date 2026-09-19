# Pilot Fast Resume

Version: 3.1.2
Status: implemented behind a disabled production feature flag

## Purpose

Remove the initial browser-session component rerun for returning signed-in
early-bird users without making a resume cookie the only authentication path.
Supabase remains authoritative for the user and company membership.

## Contract

- Cookie name: `__Host-costerly-resume-v1`.
- Cookie attributes: `Secure`, `SameSite=None`, `Partitioned`, `Path=/`.
- Maximum age and Fernet TTL: 30 minutes.
- Payload: format version, Supabase access token, Supabase refresh token, and
  token expiry, encrypted and authenticated as one Fernet blob.
- The encryption key is server-only and separate from all Supabase keys.
- The blob, keys, tokens, email, user ID, and exception text are prohibited in
  runtime telemetry.
- User and company access are still checked against Supabase after restoration.
- Existing sessionStorage restoration remains the compatibility fallback.

## Runtime outcomes

Only these safe outcome names may appear in telemetry:

- `disabled`
- `misconfigured`
- `missing`
- `invalid`
- `restored`
- `promoted_from_browser`
- `not_attempted`

## Production configuration

Deploy code first with the feature disabled. Then configure Streamlit secrets:

```toml
COSTERLY_BUILD_VERSION = "3.1.2"
COSTERLY_SESSION_SEAL_KEY = "<Fernet key>"
COSTERLY_FAST_RESUME_ENABLED = "false"
```

After the disabled deployment is healthy, switch only
`COSTERLY_FAST_RESUME_ENABLED` to `"true"` and reboot the app.

## Acceptance sequence

1. With the flag disabled, verify Refresh, Sign in, Profile, and Sign out use
   the existing sessionStorage path.
2. Enable the flag and sign in once, or complete one fallback refresh, to issue
   the encrypted cookie.
3. Run five signed-in production refreshes. Confirm one initial Python run per
   trace and `fast_resume=restored`.
4. Confirm no intermediate Streamlit screen is visible.
5. Complete two consecutive Sign out / Sign in cycles.
6. After Sign out, refresh and confirm the signed-out state remains signed out.
7. Reject a tampered and an expired blob in automated tests. Production does
   not intentionally inject corrupted authentication material.
8. Confirm telemetry contains no cookie value, token, email, or exception text.
9. Record p50 and p95 only from complete production traces.

## Rollback

Set `COSTERLY_FAST_RESUME_ENABLED = "false"` and reboot. This restores the
existing sessionStorage behavior without a code rollback. If code rollback is
also required, return to commit `28ba56b`.
